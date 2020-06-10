from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import Component

from .service import to_float

# NOTE for the implementation: share several similarities with the "cluster
# picking" scenario


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

    def _response_for_scan_destination_all(self, location, message=None):
        """Transition to the 'scan_destination_all' state

        The client screen shows a summary of all the lines and packages
        to move to a single destination.
        """
        return self._response(
            next_state="scan_destination_all",
            data=self._data_content_all_for_location(location),
            message=message,
        )

    def _response_for_start_single(
        self, location, package_level=None, line=None, message=None
    ):
        """Transition to the 'start_single' state

        The client screen shows details of the package level or move line to move.
        """
        assert package_level or line
        return self._response(
            next_state="start_single",
            data=self._data_content_line_for_location(
                location, package_level=package_level, line=line
            ),
            message=message,
        )

    def _response_for_scan_destination(
        self, location, package_level=None, line=None, message=None
    ):
        """Transition to the 'start_single' state

        The client screen shows details of the package level or move line to move.
        """
        assert package_level or line
        return self._response(
            next_state="scan_destination",
            data=self._data_content_line_for_location(
                location, package_level=package_level, line=line
            ),
            message=message,
        )

    def _data_content_all_for_location(self, location):
        return {}

    def _data_content_line_for_location(self, location, package_level=None, line=None):
        assert package_level or line
        return {}

    def start_or_recover(self):
        """Start a new session or recover an existing one

        If the current user had transfers in progress in this scenario
        and reopen the menu, we want to directly reopen the screens to choose
        destinations. Otherwise, we go to the "start" state.
        """
        # TODO if we find any stock.picking != done with current user as user id
        # and with move lines having a qty_done > 0, in the current picking types,
        # reach start_single or scan_destination_all
        return self._response_for_start()

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
        return self._response()

    def set_destination_all(self, location_id, barcode):
        """Scan destination location for all the moves of the location

        barcode is a stock.location for the destination

        Transitions:
        * scan_destination_all: invalid destination or could not set moves to done
        * start: moves are done
        """
        return self._response()

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

    def set_destination_package(self, location_id, package_level_id, barcode):
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

    def set_destination_line(self, location_id, move_line_id, quantity, barcode):
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
        }

    def set_destination_line(self):
        return {
            "location_id": {"coerce": to_int, "required": True, "type": "integer"},
            "move_line_id": {"coerce": to_int, "required": True, "type": "integer"},
            "quantity": {"coerce": to_float, "required": True, "type": "float"},
            "barcode": {"required": True, "type": "string"},
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
            "start_single": self._schema_single,
            "scan_destination": self._schema_single,
        }

    @property
    def _schema_all(self):
        package_schema = self.schemas.package()
        move_line_schema = self.schemas.move_line()
        return {
            # we'll display all the packages and move lines *without package
            # levels*
            "packages": self.schemas._schema_list_of(package_schema),
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
        return self._response_schema(next_states={"start", "scan_destination_all"})

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
        return self._response_schema(next_states={"start_single", "scan_destination"})

    def set_destination_line(self):
        return self._response_schema(next_states={"start_single", "scan_destination"})

    def postpone_package(self):
        return self._response_schema(next_states={"start_single"})

    def postpone_line(self):
        return self._response_schema(next_states={"start_single"})

    def stock_out_package(self):
        return self._response_schema(next_states={"start", "start_single"})

    def stock_out_line(self):
        return self._response_schema(next_states={"start", "start_single"})
