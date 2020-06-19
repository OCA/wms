from odoo import _

from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import Component

from .service import to_float

# NOTE for the implementation: share several similarities with the "cluster
# picking" scenario


# TODO add picking and package content in package level?


class LocationContentTransfer(Component):
    """
    Methods for the Location Content Transfer Process

    Move the full content of a location to one or another location.

    Generally used to move a pallet with multiple boxes to either:

    * 1 destination location, unloading the full pallet
    * To multiple destination locations, unloading one product/lot per
      locations
    * To multiple destination locations, unloading one product/lot per
      locations and then unloading all remaining product/lot to a single final
      destination

    The move lines must exist beforehand, the workflow only moves them.

    Expected:

    * All move lines and package level have a destination set, and are done.

    2 complementary actions are possible on the screens allowing to move a line:

    * Declare a stock out for a product or package (nothing found in the
      location)
    * Skip to the next line (will be asked again at the end)

    Flow Diagram: https://www.draw.io/#G1qRenBcezk50ggIazDuu2qOfkTsoIAxXP
    """

    _inherit = "base.shopfloor.process"
    _name = "shopfloor.location.content.transfer"
    _usage = "location_content_transfer"
    _description = __doc__

    def _response_for_start(self, message=None):
        """Transition to the 'start' state"""
        return self._response(next_state="start", message=message)

    def _response_for_scan_destination_all(self, pickings, message=None):
        """Transition to the 'scan_destination_all' state

        The client screen shows a summary of all the lines and packages
        to move to a single destination.
        """
        return self._response(
            next_state="scan_destination_all",
            data=self._data_content_all_for_location(pickings=pickings),
            message=message,
        )

    def _response_for_confirm_scan_destination_all(self, pickings, message=None):
        """Transition to the 'confirm_scan_destination_all' state

        The client screen shows a summary of all the lines and packages
        to move to a single destination. The user has to scan the destination
        location a second time to validate the destination.
        """
        return self._response(
            next_state="confirm_scan_destination_all",
            data=self._data_content_all_for_location(pickings=pickings),
            message=message,
        )

    def _response_for_start_single(self, location, next_content, message=None):
        """Transition to the 'start_single' state

        The client screen shows details of the package level or move line to move.
        """
        return self._response(
            next_state="start_single",
            data=self._data_content_line_for_location(location, next_content),
            message=message,
        )

    def _response_for_scan_destination(self, location, next_content, message=None):
        """Transition to the 'scan_destination' state

        The client screen shows details of the package level or move line to move.
        """
        return self._response(
            next_state="scan_destination",
            data=self._data_content_line_for_location(location, next_content),
            message=message,
        )

    def _response_for_confirm_scan_destination(
        self, location, next_content, message=None
    ):
        """Transition to the 'confirm_scan_destination' state

        The client screen shows details of the package level or move line to
        move. The user has to scan the destination location a second time to
        validate the destination.
        """
        return self._response(
            next_state="confirm_scan_destination",
            data=self._data_content_line_for_location(location, next_content),
            message=message,
        )

    def _data_content_all_for_location(self, pickings):
        if not pickings:
            # TODO get pickings from location
            raise NotImplementedError("to do: get pickings from location")
        sorter = self.actions_for("location_content_transfer.sorter")
        sorter.feed_pickings(pickings)
        lines = sorter.move_lines()
        package_levels = sorter.package_levels()
        return {
            "move_lines": self.data.move_lines(lines),
            "package_levels": self.data.package_levels(package_levels),
        }

    def _data_content_line_for_location(self, location, next_content):
        assert next_content._name in ("stock.move.line", "stock.package_level")
        line_data = (
            self.data.move_line(next_content)
            if next_content._name == "stock.move.line"
            else None
        )
        level_data = (
            self.data.package_level(next_content)
            if next_content._name == "stock.package_level"
            else None
        )
        return {"move_line": line_data, "package_level": level_data}

    def _next_content(self, pickings):
        sorter = self.actions_for("location_content_transfer.sorter")
        sorter.feed_pickings(pickings)
        try:
            next_content = next(sorter)
        except StopIteration:
            # TODO set picking to done
            return None
        return next_content

    def _router_single_or_all_destination(self, pickings, message=None):
        location = pickings.mapped("location_id")
        if len(pickings.mapped("move_line_ids.location_dest_id")) == 1:
            return self._response_for_scan_destination_all(pickings, message=message)
        else:
            next_content = self._next_content(pickings)
            if not next_content:
                # TODO test (no more lines)
                return self._response_for_start(
                    message=self.msg_store.location_content_transfer_complete(location)
                )
            return self._response_for_start_single(
                location, next_content, message=message
            )

    def _domain_recover_pickings(self):
        return [
            ("user_id", "=", self.env.uid),
            ("state", "in", ("assigned", "partially_available")),
            ("picking_type_id", "in", self.picking_types.ids),
        ]

    def _search_recover_pickings(self):
        candidate_pickings = self.env["stock.picking"].search(
            self._domain_recover_pickings()
        )
        started_pickings = candidate_pickings.filtered(
            lambda picking: any(line.qty_done for line in picking.move_line_ids)
        )
        return started_pickings

    def start_or_recover(self):
        """Start a new session or recover an existing one

        If the current user had transfers in progress in this scenario
        and reopen the menu, we want to directly reopen the screens to choose
        destinations. Otherwise, we go to the "start" state.
        """
        started_pickings = self._search_recover_pickings()
        if started_pickings:
            return self._router_single_or_all_destination(
                started_pickings, message=self.msg_store.recovered_previous_session()
            )
        return self._response_for_start()

    def _find_location_move_lines_domain(self, location):
        return [
            ("location_id", "=", location.id),
            ("qty_done", "=", 0),
            ("state", "in", ("assigned", "partially_available")),
        ]

    def _find_location_move_lines(self, location):
        """Find lines that potentially are to move in the location"""
        return self.env["stock.move.line"].search(
            self._find_location_move_lines_domain(location)
        )

    def scan_location(self, barcode):
        """Scan start location

        Called at the beginning at the workflow to select the location from which
        we want to move the content.

        All the move lines and package levels must have the same picking type.

        When move lines and package levels have different destinations, the
        first line without package level or package level is sent to the client.

        Transitions:
        * start: location not found, ...
        * scan_destination_all: if the destination of all the lines and package
        levels have the same destination
        * start_single: if any line or package level has a different destination
        """
        location = self.actions_for("search").location_from_scan(barcode)
        if not location:
            return self._response_for_start(message=self.msg_store.barcode_not_found())
        move_lines = self._find_location_move_lines(location)
        pickings = move_lines.mapped("picking_id")
        picking_types = pickings.mapped("picking_type_id")

        if len(picking_types) > 1:
            return self._response_for_start(
                message={
                    "message_type": "error",
                    "body": _("This location content can't be moved at once."),
                }
            )
        if picking_types - self.picking_types:
            return self._response_for_start(
                message={
                    "message_type": "error",
                    "body": _("This location content can't be moved using this menu."),
                }
            )

        for line in move_lines:
            line.qty_done = line.product_uom_qty

        pickings.user_id = self.env.uid

        return self._router_single_or_all_destination(pickings)

    def _find_transfer_move_lines_domain(self, location):
        return [
            ("location_id", "=", location.id),
            ("state", "in", ("assigned", "partially_available")),
            ("qty_done", ">", 0),
            # TODO check generated SQL
            ("picking_id.user_id", "=", self.env.uid),
        ]

    def _find_transfer_move_lines(self, location):
        """Find move lines currently being moved by the user"""
        lines = self.env["stock.move.line"].search(
            self._find_transfer_move_lines_domain(location)
        )
        return lines

    def _set_destination_lines(self, pickings, move_lines, dest_location):
        move_lines.location_dest_id = dest_location
        move_lines.package_level_id.location_dest_id = dest_location
        pickings.action_done()

    def set_destination_all(self, location_id, barcode, confirmation=False):
        """Scan destination location for all the moves of the location

        barcode is a stock.location for the destination

        Transitions:
        * scan_destination_all: invalid destination or could not set moves to done
        * start: moves are done
        """
        location = self.env["stock.location"].browse(location_id)
        if not location.exists():
            return self._response_for_start(message=self.msg_store.record_not_found())
        move_lines = self._find_transfer_move_lines(location)
        pickings = move_lines.mapped("picking_id")
        scanned_location = self.actions_for("search").location_from_scan(barcode)
        if not scanned_location:
            return self._response_for_scan_destination_all(
                pickings, message=self.msg_store.barcode_not_found()
            )

        if not scanned_location.is_sublocation_of(
            self.picking_types.mapped("default_location_dest_id")
        ):
            return self._response_for_scan_destination_all(
                pickings, message=self.msg_store.dest_location_not_allowed()
            )
        if not confirmation and not scanned_location.is_sublocation_of(
            move_lines.mapped("location_dest_id")
        ):
            # the scanned location is valid (child of picking type's destination)
            # but not the expected one: ask for confirmation
            return self._response_for_confirm_scan_destination_all(pickings)

        self._set_destination_lines(pickings, move_lines, scanned_location)

        return self._response_for_start(
            message={
                "message_type": "success",
                "body": _("Content transferred from {}.").format(location.name),
            }
        )

    def go_to_single(self, location_id):
        """Ask the first move line or package level

        If the user was brought to the screen allowing to move everything to
        the same location, but they want to move them to different locations,
        this method will return the first move line or package level.

        Transitions:
        * start: no remaining lines in the location
        * start_single: if any line or package level has a different destination
        """
        return self._response()

    def scan_package(self, location_id, package_level_id, barcode):
        """Scan a package level to move

        It validates that the user scanned the correct package, lot or product.

        Transitions:
        * start: no remaining lines in the location
        * start_single: barcode not found, ...
        * scan_destination: the barcode matches
        """
        return self._response()

    def scan_line(self, location_id, move_line_id, barcode):
        """Scan a move line to move

        It validates that the user scanned the correct package, lot or product.

        Transitions:
        * start: no remaining lines in the location
        * start_single: barcode not found, ...
        * scan_destination: the barcode matches
        """
        return self._response()

    def set_destination_package(
        self, location_id, package_level_id, barcode, confirmation=False
    ):
        """Scan destination location for package level

        If the move has other move lines / package levels it has to be split
        so we can post only this part.

        After the destination is set, the move is set to done.

        Beware, when _action_done() is called on the move, the normal behavior
        of Odoo would be to create a backorder transfer. We don't want this or
        we would have a backorder per move. The context key
        ``_sf_no_backorder`` disables the creation of backorders, it must be set
        on all moves, but the last one of a transfer (so in case something was not
        available, a backorder is created).

        Transitions:
        * scan_destination: invalid destination or could not
        * start_single: continue with the next package level / line
        """
        return self._response()

    def set_destination_line(
        self, location_id, move_line_id, quantity, barcode, confirmation=False
    ):
        """Scan destination location for move line

        If the quantity < qty of the line, split the move and reserve it.
        If the move has other move lines / package levels it has to be split
        so we can post only this part.

        After the destination and quantity are set, the move is set to done.

        Beware, when _action_done() is called on the move, the normal behavior
        of Odoo would be to create a backorder transfer. We don't want this or
        we would have a backorder per move. The context key
        ``_sf_no_backorder`` disables the creation of backorders, it must be set
        on all moves, but the last one of a transfer (so in case something was not
        available, a backorder is created).

        Transitions:
        * scan_destination: invalid destination or could not
        * start_single: continue with the next package level / line
        """
        return self._response()

    def postpone_package(self, location_id, package_level_id):
        """Mark a package level as postponed and return the next level/line

        NOTE for implementation: Use the field "shopfloor_postponed", which has
        to be included in the sort to get the next lines.

        Transitions:
        * start_single: continue with the next package level / line
        """
        return self._response()

    def postpone_line(self, location_id, move_line_id):
        """Mark a move line as postponed and return the next level/line

        NOTE for implementation: Use the field "shopfloor_postponed", which has
        to be included in the sort to get the next lines.

        Transitions:
        * start_single: continue with the next package level / line
        """
        return self._response()

    def stock_out_package(self, location_id, package_level_id):
        """Declare a stock out on a package level

        It first ensures the stock.move only has this package level. If not, it
        splits the move to have no side-effect on the other package levels/move
        lines.

        It unreserves the move, create an inventory at 0 in the move's source
        location, create a second draft inventory (if none exists) to check later.
        Finally, it cancels the move.

        Transitions:
        * start: no more content to move
        * start_single: continue with the next package level / line
        """
        return self._response()

    def stock_out_line(self, location_id, move_line_id):
        """Declare a stock out on a move line

        It first ensures the stock.move only has this move line. If not, it
        splits the move to have no side-effect on the other package levels/move
        lines.

        It unreserves the move, create an inventory at 0 in the move's source
        location, create a second draft inventory (if none exists) to check later.
        Finally, it cancels the move.

        Transitions:
        * start: no more content to move
        * start_single: continue with the next package level / line
        """
        return self._response()


class ShopfloorLocationContentTransferValidator(Component):
    """Validators for the Location Content Transfer endpoints"""

    _inherit = "base.shopfloor.validator"
    _name = "shopfloor.location.content.transfer.validator"
    _usage = "location_content_transfer.validator"

    def start_or_recover(self):
        return {}

    def scan_location(self):
        return {"barcode": {"required": True, "type": "string"}}

    def set_destination_all(self):
        return {
            "location_id": {"coerce": to_int, "required": True, "type": "integer"},
            "barcode": {"required": True, "type": "string"},
            "confirmation": {"type": "boolean", "nullable": True, "required": False},
        }

    def go_to_single(self):
        return {"location_id": {"coerce": to_int, "required": True, "type": "integer"}}

    def scan_package(self):
        return {
            "location_id": {"coerce": to_int, "required": True, "type": "integer"},
            "package_level_id": {"coerce": to_int, "required": True, "type": "integer"},
            "barcode": {"required": True, "type": "string"},
        }

    def scan_line(self):
        return {
            "location_id": {"coerce": to_int, "required": True, "type": "integer"},
            "move_line_id": {"coerce": to_int, "required": True, "type": "integer"},
            "barcode": {"required": True, "type": "string"},
        }

    def set_destination_package(self):
        return {
            "location_id": {"coerce": to_int, "required": True, "type": "integer"},
            "package_level_id": {"coerce": to_int, "required": True, "type": "integer"},
            "barcode": {"required": True, "type": "string"},
            "confirmation": {"type": "boolean", "nullable": True, "required": False},
        }

    def set_destination_line(self):
        return {
            "location_id": {"coerce": to_int, "required": True, "type": "integer"},
            "move_line_id": {"coerce": to_int, "required": True, "type": "integer"},
            "quantity": {"coerce": to_float, "required": True, "type": "float"},
            "barcode": {"required": True, "type": "string"},
            "confirmation": {"type": "boolean", "nullable": True, "required": False},
        }

    def postpone_package(self):
        return {
            "location_id": {"coerce": to_int, "required": True, "type": "integer"},
            "package_level_id": {"coerce": to_int, "required": True, "type": "integer"},
        }

    def postpone_line(self):
        return {
            "location_id": {"coerce": to_int, "required": True, "type": "integer"},
            "move_line_id": {"coerce": to_int, "required": True, "type": "integer"},
        }

    def stock_out_package(self):
        return {
            "location_id": {"coerce": to_int, "required": True, "type": "integer"},
            "package_level_id": {"coerce": to_int, "required": True, "type": "integer"},
        }

    def stock_out_line(self):
        return {
            "location_id": {"coerce": to_int, "required": True, "type": "integer"},
            "move_line_id": {"coerce": to_int, "required": True, "type": "integer"},
        }


class ShopfloorLocationContentTransferValidatorResponse(Component):
    """Validators for the Location Content Transfer endpoints responses"""

    _inherit = "base.shopfloor.validator.response"
    _name = "shopfloor.location.content.transfer.validator.response"
    _usage = "location_content_transfer.validator.response"

    def _states(self):
        """List of possible next states

        With the schema of the data send to the client to transition
        to the next state.
        """
        return {
            "start": {},
            "scan_destination_all": self._schema_all,
            "confirm_scan_destination_all": self._schema_all,
            "start_single": self._schema_single,
            "scan_destination": self._schema_single,
            "confirm_scan_destination": self._schema_single,
        }

    @property
    def _schema_all(self):
        package_level_schema = self.schemas.package_level()
        move_line_schema = self.schemas.move_line()
        return {
            # we'll display all the packages and move lines *without package
            # levels*
            "package_levels": self.schemas._schema_list_of(package_level_schema),
            "move_lines": self.schemas._schema_list_of(move_line_schema),
        }

    @property
    def _schema_single(self):
        schema_package_level = self.schemas.package_level()
        schema_move_line = self.schemas.move_line()
        return {
            # we'll have one or the other...
            # TODO add the package in the package_level
            "package_level": self.schemas._schema_dict_of(schema_package_level),
            "move_line": self.schemas._schema_dict_of(schema_move_line),
        }

    def start_or_recover(self):
        return self._response_schema(
            next_states={"start", "scan_destination_all", "start_single"}
        )

    def scan_location(self):
        return self._response_schema(
            next_states={"start", "scan_destination_all", "start_single"}
        )

    def set_destination_all(self):
        return self._response_schema(
            next_states={
                "start",
                "scan_destination_all",
                "confirm_scan_destination_all",
            }
        )

    def go_to_single(self):
        return self._response_schema(next_states={"start", "start_single"})

    def scan_package(self):
        return self._response_schema(
            next_states={"start", "start_single", "scan_destination"}
        )

    def scan_line(self):
        return self._response_schema(
            next_states={"start", "start_single", "scan_destination"}
        )

    def set_destination_package(self):
        return self._response_schema(
            next_states={"start_single", "scan_destination", "confirm_scan_destination"}
        )

    def set_destination_line(self):
        return self._response_schema(
            next_states={"start_single", "scan_destination", "confirm_scan_destination"}
        )

    def postpone_package(self):
        return self._response_schema(next_states={"start_single"})

    def postpone_line(self):
        return self._response_schema(next_states={"start_single"})

    def stock_out_package(self):
        return self._response_schema(next_states={"start", "start_single"})

    def stock_out_line(self):
        return self._response_schema(next_states={"start", "start_single"})
