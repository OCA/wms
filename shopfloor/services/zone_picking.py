from odoo.addons.base_rest.components.service import to_bool, to_int
from odoo.addons.component.core import Component

from .service import to_float


class ZonePicking(Component):
    """
    Methods for the Zone Picking Process

    Zone picking of move lines.

    Note:

    * Several operation types could be linked to a single menu item
    * If several operator work in a same zone, they’ll see the same move lines but
      will only posts theirs when unloading their goods, which means that when they
      scan lines, the backend has to store the user id on the move lines

    Workflow:

    1. The operator scans the zone location with goods to pick (zone location
       meaning a parent location, not a leaf)
    2. If the zone contains lines from different picking types, the operator
       chooses the type to work with
    3. The client application shows the list of move lines, with an option
       to choose the sorting of the lines
    4. The operator selects a line to pick, by scanning one of:

       * location, if only a single move line there; if a location is scanned
         and it contains several move lines, the view is updated to show only
         them
       * package
       * product
       * lot

    5. The operator scans the destination for the line they scanned, this is where
       the path splits:

       * they scan a location, in which case the move line's destination is
         updated with it and the move is done
       * they scan a package, which becomes the destination package of the move
         line, the move line is not set to done, its ``qty_done`` is updated
         and a field ``shopfloor_user_id`` is set to the user; consider the
         move line is set in a buffer

    6. At any point, from the list of moves, the operator can reach the
       "unload" screens to unload what they had put into the buffer (scanned a
       destination package during step 5.). This is optional as they can directly
       move whole pallets by scanning the destination in step 5.
    7. The unload screens (similar to those of the Cluster Picking workflow) are
       used to move what has been put in the buffer:

       * if the original destination of all the lines is unique, screen allows
         to scan a single destination; they can use a "split" button to go to
         the line by line screen
       * if the lines have different destinations, they have to scan the destination
         package, then scan the destination location, scan the next package and its
         destination and so on.

    The list of move lines (point 4.) has support functions:

    * Change a lot or pack: if the expected lot is at the very bottom of the
      location or a stock error forces a user to change lot or pack, user can
      do it during the picking.
    * Declare stock out: if a good is in fact not in stock or only partially.
      Note the move lines may become unavailable or partially unavailable and
      generate a back-order.

    """

    _inherit = "base.shopfloor.process"
    _name = "shopfloor.zone.picking"
    _usage = "zone_picking"
    _description = __doc__

    def _response_for_start(self, message=None):
        return self._response(next_state="start", message=message)

    def _response_for_select_picking_type(
        self, zone_location, picking_types, message=None
    ):
        return self._response(
            next_state="select_picking_type",
            data=self._data_for_select_picking_type(zone_location, picking_types),
            message=message,
        )

    def _response_for_select_line(
        self, zone_location, picking_type, move_lines, message=None, popup=None
    ):
        return self._response(
            next_state="select_line",
            data=self._data_for_move_lines(zone_location, picking_type, move_lines),
            message=message,
            popup=popup,
        )

    def _response_for_set_line_destination(
        self, zone_location, picking_type, move_line, message=None
    ):
        return self._response(
            next_state="set_line_destination",
            data=self._data_for_move_line(zone_location, picking_type, move_line),
            message=message,
        )

    def _response_for_confirm_set_line_destination(
        self, zone_location, picking_type, move_line, message=None
    ):
        return self._response(
            next_state="confirm_set_line_destination",
            data=self._data_for_move_line(zone_location, picking_type, move_line),
            message=message,
        )

    def _response_for_zero_check(
        self, zone_location, picking_type, location, message=None
    ):
        return self._response(
            next_state="zero_check",
            data=self._data_for_move_line(zone_location, picking_type, location),
            message=message,
        )

    def _response_for_change_pack_lot(
        self, zone_location, picking_type, move_line, message=None
    ):
        return self._response(
            next_state="change_pack_lot",
            data=self._data_for_move_line(zone_location, picking_type, move_line),
            message=message,
        )

    def _response_for_unload_all(
        self, zone_location, picking_type, move_lines, message=None
    ):
        return self._response(
            next_state="unload_all",
            data=self._data_for_move_lines(zone_location, picking_type, move_lines),
            message=message,
        )

    def _response_for_confirm_unload_all(
        self, zone_location, picking_type, move_lines, message=None
    ):
        return self._response(
            next_state="confirm_unload_all",
            data=self._data_for_move_lines(zone_location, picking_type, move_lines),
            message=message,
        )

    def _response_for_unload_single(
        self, zone_location, picking_type, move_line, message=None, popup=None
    ):
        return self._response(
            next_state="unload_single",
            data=self._data_for_move_line(zone_location, picking_type, move_line),
            message=message,
            popup=popup,
        )

    def _response_for_unload_set_destination(
        self, zone_location, picking_type, move_line, message=None
    ):
        return self._response(
            next_state="unload_set_destination",
            data=self._data_for_move_line(zone_location, picking_type, move_line),
            message=message,
        )

    def _response_for_confirm_unload_set_destination(
        self, zone_location, picking_type, move_line
    ):
        return self._response(
            next_state="confirm_unload_set_destination",
            data=self._data_for_move_line(zone_location, picking_type, move_line),
        )

    def _data_for_select_picking_type(self, zone_location, picking_types):
        return {
            "zone_location": self.data.location(zone_location),
            # available picking types to choose from
            # TODO add lines count and priority lines count in the data
            "picking_types": self.data.picking_types(picking_types),
        }

    def _data_for_move_line(self, zone_location, picking_type, move_line):
        return {
            "zone_location": self.data.location(zone_location),
            "picking_type": self.data.picking_type(picking_type),
            "move_line": self.data.move_line(move_line),
        }

    def _data_for_move_lines(self, zone_location, picking_type, move_lines):
        return {
            "zone_location": self.data.location(zone_location),
            "picking_type": self.data.picking_type(picking_type),
            # TODO sorting, ... (but maybe the lines are already sorted when passed)
            "move_lines": self.data.move_lines(move_lines),
        }

    def scan_location(self, barcode):
        """Scan the zone location where the picking should occur

        The location must be a sub-location of one of the picking types'
        default destination locations of the menu.

        Transitions:
        * start: invalid barcode
        * select_picking_type: the location is valid, user has to choose a picking type
        """
        return self._response()

    def list_move_lines(self, zone_location_id, picking_type_id, order="priority"):
        """List all move lines to pick, sorted

        Transitions:
        * select_line: show the list of move lines
        """
        return self._response()

    def scan_source(self, zone_location_id, picking_type_id, barcode, order="priority"):
        """Select a move line or narrow the list of move lines

        When the barcode is a location and we can unambiguously know which move
        line is picked (the quants in the location has one product/lot/package,
        matching a single move line), then the move line is selected.
        Otherwise, the list of move lines is refreshed with a filter on the
        scanned location, showing the move lines that have this location as
        source.

        When the barcode is a package, a product or a lot, the first matching
        line is selected.

        A selected line goes to the next screen to select the destination
        location or package.

        Transitions:
        * select_line: barcode not found or narrow the list on a location
        * set_line_destination: a line has been selected for picking
        """
        return self._response()

    def set_destination(
        self,
        zone_location_id,
        picking_type_id,
        move_line_id,
        barcode,
        quantity,
        confirmation=False,
    ):
        """Set a destination location (and done) or a destination package (in buffer)

        When a line is picked, it can either:

        * be moved directly to a destination location, typically a pallet
        * be moved to a destination package, that we'll call buffer in the docstrings

        When the barcode is a valid location, actions on the move line:

        * destination location set to the scanned one
        * the quantity done is set to the passed quantity
        * if the move has other move lines, it is split to have only this move line
        * set to done (without backorder)

        A valid location is a sub-location of the original destination, or a
        sub-location of the picking type's default destination location if
        ``confirmation`` is True.

        When the barcode is a valid package, actions on the move line:

        * destination package is set to the scanned one
        * the quantity done is set to the passed quantity
        * the field ``shopfloor_user_id`` is updated with the current user

        Those fields will be used to identify which move lines are in the buffer.

        A valid package is:

        * an empty package
        * not used as destination for another move line

        Transitions:
        * select_line: destination has been set, showing the next lines to pick
        * zero_check: if the quantity of product moved is 0 in the source
          location after the move (beware: at this point the product we put in
          the buffer is still considered to be in the source location, so we
          have to compute the source location's quantity - qty_done).
        * set_line_destination: the scanned location is invalid, user has to
          scan another one
        * confirm_set_line_destination: the scanned location is not in the
          expected one but is valid (in picking type's default destination)
        """
        # TODO on _action_done, use ``_sf_no_backorder`` in the
        # context to disable backorders (see override in stock_picking.py).
        return self._response()

    def is_zero(self, zone_location_id, picking_type_id, move_line_id, zero):
        """Confirm or not if the source location of a move has zero qty

        If the user confirms there is zero quantity, it means the stock was
        correct and there is nothing to do. If the user says "no", a draft
        empty inventory is created for the product (with lot if tracked).

        Transitions:
        * select_line: whether the user confirms or not the location is empty,
          go back to the picking of lines
        """
        # TODO look in cluster_picking.py, same function exists
        return self._response()

    def stock_issue(self, zone_location_id, picking_type_id, move_line_id):
        """Declare a stock issue for a line

        After errors in the stock, the user cannot take all the products
        because there is physically not enough goods. The move line is deleted
        (unreserve), and an inventory is created to reduce the quantity in the
        source location to prevent future errors until a correction. Beware:
        the quantity already reserved and having a qty_done set on other lines
        in the same location should remain reserved so the inventory's quantity
        must be set to the total of qty_done of other lines.

        The other lines not yet picked (no qty_done) in the same location for
        the same product, lot, package are unreserved as well (moves lines
        deleted, which unreserve their quantity on the move).

        A second inventory is created in draft to have someone do an inventory
        check.

        At the end, it tries to reserve the goods again, and if the current
        line could be reserved in the current zone location, it transitions
        directly to the screen to set the destination.

        Transitions:
        * select_line: go back to the picking of lines for the next ones (nothing
          could be reserved as replacement)
        * set_line_destination: something could be reserved instead of the original
          move line
        """
        # TODO look in cluster_picking.py, similar function exists
        return self._response()

    def change_pack_lot(self, zone_location_id, picking_type_id, move_line_id, barcode):
        """Change the source package or the lot of a move line

        If the expected lot or package is at the very bottom of the location or
        a stock error forces a user to change lot or package, user can change the
        package or lot of the current move line.

        If the pack or lot was not supposed to be in the source location,
        a draft inventory is created to have this checked.

        Transitions:
        * change_pack_lot: the barcode scanned is invalid or change could not be done
        * set_line_destination: the package / lot has been changed, can be
          moved to destination now
        * select_line: if the move line does not exist anymore
        """
        # TODO look in cluster_picking.py, similar function exists
        return self._response()

    def prepare_unload(self, zone_location_id, picking_type_id):
        """Initiate the unloading of the buffer

        The buffer is composed of move lines:

        * in the current zone location and picking type
        * not done or canceled
        * with a qty_done > 0
        * have a destination package
        * with ``shopfloor_user_id`` equal to the current user

        The lines are grouped by their destination package. The destination
        package is what is shown on the screen (with their content, which is
        the move lines with the package as destination), and this is what is
        passed along in the ``package_id`` parameters in the unload methods.

        It goes to different screens depending if there is only one move line,
        or if all the move lines have the same destination or not.

        Transitions:
        * unload_single: move lines have different destinations, return data
          for the next destination package
        * unload_set_destination: there is only one move line in the buffer
        * unload_all: the move lines in the buffer all have the same
          destination location
        * select_line: no remaining move lines in buffer
        """
        return self._response()

    def set_destination_all(
        self, zone_location_id, picking_type_id, barcode, confirmation=False
    ):
        """Set the destination for all the lines in the buffer

        Look in ``prepare_unload`` for the definition of the buffer.

        This method must be used only if all the buffer's move lines which have
        a destination package, qty done > 0, and have the same destination
        location.

        A scanned location outside of the source location of the operation type is
        invalid.

        The move lines are then set to done, without backorders.

        Transitions:
        * unload_all: the scanned destination is invalid, user has to
          scan another one
        * confirm_unload_all: the scanned location is not in the
          expected one but is valid (in picking type's default destination)
        * select_line: no remaining move lines in buffer
        """
        return self._response()

    def unload_split(self, zone_location_id, picking_type_id):
        """Indicates that now the buffer must be treated line per line

        Called from a button, users decides to handle destinations one by one.
        Even if the move lines to unload all have the same destination.

        Look in ``prepare_unload`` for the definition of the buffer.

        Transitions:
        * unload_single: more than one remaining line in the buffer
        * unload_set_destination: there is only one remaining line in the buffer
        * select_line: no remaining move lines in buffer
        """
        return self._response()

    def unload_scan_pack(self, zone_location_id, picking_type_id, package_id, barcode):
        """Scan the destination package to check user moves the good one

        The "unload_single" screen proposes a package (which has been
        previously been set as destination package of lines of the buffer).
        The user has to scan the package to validate they took the good one.

        Transitions:
        * unload_single: the scanned barcode does not match the package
        * unload_set_destination: the scanned barcode matches the package
        * confirm_unload_set_destination: the scanned location is not in the
          expected one but is valid (in picking type's default destination)
        * select_line: no remaining move lines in buffer
        """
        return self._response()

    def unload_set_destination(
        self, zone_location_id, picking_type_id, package_id, barcode, confirmation=False
    ):
        """Scan the final destination for move lines in the buffer with the
        destination package

        All the move lines in the buffer with the package_id as destination
        package are updated with the scanned location.

        The move lines are then set to done, without backorders.

        Look in ``prepare_unload`` for the definition of the buffer.

        Transitions:
        * unload_single: buffer still contains move lines, unload the next package
        * unload_set_destination: the scanned location is invalid, user has to
          scan another one
        * confirm_unload_set_destination: the scanned location is not in the
          expected one but is valid (in picking type's default destination)
        * select_line: no remaining move lines in buffer
        """
        # TODO on _action_done, use ``_sf_no_backorder`` in the
        # context to disable backorders (see override in stock_picking.py).
        # TODO return a popup with completion info alongside the response,
        # see in cluster_picking.py how it's done
        return self._response()


class ShopfloorZonePickingValidator(Component):
    """Validators for the Zone Picking endpoints"""

    _inherit = "base.shopfloor.validator"
    _name = "shopfloor.zone_picking.validator"
    _usage = "zone_picking.validator"

    def scan_location(self):
        return {"barcode": {"required": True, "type": "string"}}

    def list_move_lines(self):
        return {
            "zone_location_id": {"coerce": to_int, "required": True, "type": "integer"},
            "picking_type_id": {"coerce": to_int, "required": True, "type": "integer"},
            "barcode": {"required": False, "nullable": True, "type": "string"},
            "order": {
                "required": False,
                "type": "string",
                "allowed": ["priority", "location"],
            },
        }

    def scan_source(self):
        return {
            "zone_location_id": {"coerce": to_int, "required": True, "type": "integer"},
            "picking_type_id": {"coerce": to_int, "required": True, "type": "integer"},
            "barcode": {"required": False, "nullable": True, "type": "string"},
            "order": {
                "required": False,
                "type": "string",
                "allowed": ["priority", "location"],
            },
        }

    def set_destination(self):
        return {
            "zone_location_id": {"coerce": to_int, "required": True, "type": "integer"},
            "picking_type_id": {"coerce": to_int, "required": True, "type": "integer"},
            "barcode": {"required": False, "nullable": True, "type": "string"},
            "order": {
                "required": False,
                "type": "string",
                "allowed": ["priority", "location"],
            },
            "quantity": {"coerce": to_float, "required": True, "type": "float"},
            "confirmation": {"type": "boolean", "nullable": True, "required": False},
        }

    def is_zero(self):
        return {
            "zone_location_id": {"coerce": to_int, "required": True, "type": "integer"},
            "picking_type_id": {"coerce": to_int, "required": True, "type": "integer"},
            "move_line_id": {"coerce": to_int, "required": True, "type": "integer"},
            "zero": {"coerce": to_bool, "required": True, "type": "boolean"},
        }

    def stock_issue(self):
        return {
            "zone_location_id": {"coerce": to_int, "required": True, "type": "integer"},
            "picking_type_id": {"coerce": to_int, "required": True, "type": "integer"},
            "move_line_id": {"coerce": to_int, "required": True, "type": "integer"},
        }

    def change_pack_lot(self):
        return {
            "zone_location_id": {"coerce": to_int, "required": True, "type": "integer"},
            "picking_type_id": {"coerce": to_int, "required": True, "type": "integer"},
            "move_line_id": {"coerce": to_int, "required": True, "type": "integer"},
            "barcode": {"required": False, "nullable": True, "type": "string"},
        }

    def prepare_unload(self):
        return {
            "zone_location_id": {"coerce": to_int, "required": True, "type": "integer"},
            "picking_type_id": {"coerce": to_int, "required": True, "type": "integer"},
        }

    def set_destination_all(self):
        return {
            "zone_location_id": {"coerce": to_int, "required": True, "type": "integer"},
            "picking_type_id": {"coerce": to_int, "required": True, "type": "integer"},
            "barcode": {"required": False, "nullable": True, "type": "string"},
            "confirmation": {"type": "boolean", "nullable": True, "required": False},
        }

    def unload_split(self):
        return {
            "zone_location_id": {"coerce": to_int, "required": True, "type": "integer"},
            "picking_type_id": {"coerce": to_int, "required": True, "type": "integer"},
        }

    def unload_scan_pack(self):
        return {
            "zone_location_id": {"coerce": to_int, "required": True, "type": "integer"},
            "picking_type_id": {"coerce": to_int, "required": True, "type": "integer"},
            "package_id": {"coerce": to_int, "required": True, "type": "integer"},
        }

    def unload_set_destination(self):
        return {
            "zone_location_id": {"coerce": to_int, "required": True, "type": "integer"},
            "picking_type_id": {"coerce": to_int, "required": True, "type": "integer"},
            "package_id": {"coerce": to_int, "required": True, "type": "integer"},
            "barcode": {"required": False, "nullable": True, "type": "string"},
            "confirmation": {"type": "boolean", "nullable": True, "required": False},
        }


class ShopfloorZonePickingValidatorResponse(Component):
    """Validators for the Zone Picking endpoints responses"""

    _inherit = "base.shopfloor.validator.response"
    _name = "shopfloor.zone_picking.validator.response"
    _usage = "zone_picking.validator.response"

    def _states(self):
        """List of possible next states

        With the schema of the data send to the client to transition
        to the next state.
        """
        return {
            "start": {},
            "select_picking_type": self._schema_for_select_picking_type,
            "select_line": self._schema_for_move_lines,
            "set_line_destination": self._schema_for_move_line,
            "confirm_set_line_destination": self._schema_for_move_line,
            "zero_check": self._schema_for_move_line,
            "change_pack_lot": self._schema_for_move_line,
            "unload_all": self._schema_for_move_lines,
            "confirm_unload_all": self._schema_for_move_lines,
            "unload_single": self._schema_for_move_line,
            "unload_set_destination": self._schema_for_move_line,
            "confirm_unload_set_destination": self._schema_for_move_line,
        }

    def scan_location(self):
        return self._response_schema(next_states={"start", "select_picking_type"})

    def list_move_lines(self):
        return self._response_schema(next_states={"select_line"})

    def scan_source(self):
        return self._response_schema(
            next_states={"select_line", "set_line_destination"}
        )

    def set_destination(self):
        return self._response_schema(
            next_states={
                "select_line",
                "set_line_destination",
                "confirm_set_line_destination",
                "zero_check",
            }
        )

    def is_zero(self):
        return self._response_schema(next_states={"select_line"})

    def stock_issue(self):
        return self._response_schema(
            next_states={"select_line", "set_line_destination"}
        )

    def change_pack_lot(self):
        return self._response_schema(
            next_states={"change_pack_lot", "set_line_destination", "select_line"}
        )

    def prepare_unload(self):
        return self._response_schema(
            next_states={
                "unload_all",
                "unload_single",
                "unload_set_destination",
                "select_line",
            }
        )

    def set_destination_all(self):
        return self._response_schema(
            next_states={"unload_all", "confirm_unload_all", "select_line"}
        )

    def unload_split(self):
        return self._response_schema(
            next_states={"unload_single", "unload_set_destination", "select_line"}
        )

    def unload_scan_pack(self):
        return self._response_schema(
            next_states={"unload_single", "unload_set_destination", "select_line"}
        )

    def unload_set_destination(self):
        return self._response_schema(
            next_states={
                "unload_single",
                "unload_set_destination",
                "confirm_unload_set_destination",
                "select_line",
            }
        )

    @property
    def _schema_for_select_picking_type(self):
        schema = {
            "zone_location": self.schemas._schema_dict_of(self.schemas.location()),
            "picking_types": self.schemas._schema_list_of(self.schemas.picking_type()),
        }
        return schema

    @property
    def _schema_for_move_line(self):
        schema = {
            "zone_location": self.schemas._schema_dict_of(self.schemas.location()),
            "picking_type": self.schemas._schema_dict_of(self.schemas.picking_type()),
            "move_line": self.schemas._schema_dict_of(self.schemas.move_line()),
        }
        return schema

    @property
    def _schema_for_move_lines(self):
        schema = {
            "zone_location": self.schemas._schema_dict_of(self.schemas.location()),
            "picking_type": self.schemas._schema_dict_of(self.schemas.picking_type()),
            "move_lines": self.schemas._schema_list_of(self.schemas.move_line()),
        }
        return schema
