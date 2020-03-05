from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import Component

from .service import to_float


class Checkout(Component):
    """
    Methods for the Checkout Process

    This process runs on existing moves.
    It happens on the "Packing" step of a pick/pack/ship.

    Use cases:

    1) Products are packed (e.g. full pallet shipping) and we keep the packages
    2) Products are packed (e.g. rollercage bins) and we create a new package
       with same content for shipping
    3) Products are packed (e.g. half-pallet ) and we merge several into one
    4) Products are packed (e.g. too high pallet) and we split it on several
    5) Products are not packed (e.g. raw products) and we create new packages
    6) Products are not packed (e.g. raw products) and we do not create packages

    Flow Diagram: https://www.draw.io/#G1qRenBcezk50ggIazDuu2qOfkTsoIAxXP
    """

    _inherit = "base.shopfloor.service"
    _name = "shopfloor.checkout"
    _usage = "checkout"
    _description = __doc__

    def scan_document(self, barcode):
        """Scan a package, a stock.picking or a location

        When a location is scanned, if all the move lines from this destination
        are for the same stock.picking, the stock.picking is used for the
        next steps.

        When a package is scanned, if the package has a move line to move it
        from a location/sublocation of the current stock.picking.type, the
        stock.picking for the package is used for the next steps.

        When a stock.picking is scanned, it is used for the next steps.

        In every case above, the stock.picking must be entirely available and
        must match the current picking type.

        Transitions:
        * select_document: when no stock.picking could be found
        * select_line: a stock.picking is selected
        """
        return self._response()

    def list_stock_picking(self):
        """List stock.picking records available

        Returns a list of all the available records for the current picking
        type.

        Transitions:
        * manual_selection: to the selection screen
        """
        return self._response()

    def select(self, picking_id):
        """Select a stock picking for the process

        Used from the list of stock pickings (manual_selection), from there,
        the user can click on a stock.picking record which calls this method.

        The ``list_stock_picking`` returns only the valid records (same picking
        type, fully available, ...), but this method has to check again in case
        something changed since the list was sent to the client.

        Transitions:
        * manual_selection: stock.picking could finally not be selected (not
          available, ...)
        * summary: goes straight to this state used to set the moves as done when
          all the move lines with a reserved quantity have a 'quantity done'
        * select_line: the "normal" case, when the user has to put in pack/move
          lines
        """
        return self._response()

    def scan_line(self, picking_id, barcode):
        """Scan move lines of the stock picking

        It allows to select move lines of the stock picking for the next
        screen. Lines can be found either by scanning a package, a product or a
        lot.

        There should be no ambiguity, so for instance if a product is scanned but
        several packs contain it, the endpoint will ask to scan a pack; if the
        product is tracked by lot, to scan a lot.

        Once move lines are found, their ``qty_done`` is set to their reserved
        quantity.

        Transitions:
        * select_line: nothing could be found for the barcode
        * select_pack: lines are selected, user is redirected to this
        screen to change the qty done and destination pack if needed
        """
        return self._response()

    def select_line(self, picking_id, package_id=None, move_line_id=None):
        """Select move lines of the stock picking

        This is the same as ``scan_line``, except that a package id or a
        move_line_id is given by the client (user clicked on a list).

        It returns a list of move line ids that will be displayed by the
        screen ``select_pack``. This screen will have to send this list to
        the endpoints it calls, so we can select/deselect lines but still
        show them in the list of the client application.

        Transitions:
        * select_line: nothing could be found for the barcode
        * select_pack: lines are selected, user is redirected to this
        screen to change the qty done and destination pack if needed
        """
        assert package_id or move_line_id
        return self._response()

    def reset_line_qty(self, move_line_id):
        """Reset qty_done of a move line to zero

        Used to deselect a line in the "select_pack" screen.

        Transitions:
        * select_pack: goes back to the same state, the line will appear
        as deselected
        """
        return self._response()

    def set_line_qty(self, move_line_id):
        """Set qty_done of a move line to its reserved quantity

        Used to deselect a line in the "select_pack" screen.

        Transitions:
        * select_pack: goes back to the same state, the line will appear
        as selected
        """
        return self._response()

    def scan_pack_action(self, move_line_ids, barcode):
        """Scan a package, a lot, a product or a package to handle a line

        When a package is scanned, if the package is known as the destination
        package of one of the lines or is the source package of a selected
        line, the package is set to be the destination package of all then
        selected lines.

        When a product is scanned, it selects (set qty_done = reserved qty) or
        deselects (set qty_done = 0) the move lines for this product. Only
        products not tracked by lot can use this.

        When a lot is scanned, it does the same as for the products but based
        on the lot.

        When a packaging type (one without related product) is scanned, a new
        package is created and set as destination of the selected lines.

        Selected lines are move lines in the list of ``move_line_ids`` where
        ``qty_done`` > 0 and have no destination package.

        Transitions:
        * select_pack: when a product or lot is scanned to select/deselect,
        the client app has to show the same screen with the updated selection
        * select_line: when a package or packaging type is scanned, move lines
        have been put in package and we can return back to this state to handle
        the other lines
        * summary: if there is no other lines, go to the summary screen to be able
        to close the stock picking
        """
        return self._response()

    def set_custom_qty(self, move_line_id, qty_done):
        """Change qty_done of a move line with a custom value

        Transitions:
        * select_pack: goes back to this screen showing all the lines after
          we changed the qty
        """
        return self._response()

    def new_package(self, move_line_ids):
        """Add all selected lines in a new package

        It creates a new package and set it as the destination package of all
        the selected lines.

        Selected lines are move lines in the list of ``move_line_ids`` where
        ``qty_done`` > 0 and have no destination package.

        Transitions:
        * select_line: goes back to selection of lines to work on next lines
        """
        return self._response()

    # TODO add the rest of the methods


class ShopfloorCheckoutValidator(Component):
    """Validators for the Checkout endpoints"""

    _inherit = "base.shopfloor.validator"
    _name = "shopfloor.checkout.validator"
    _usage = "checkout.validator"

    def scan_document(self):
        return {"barcode": {"required": True, "type": "string"}}

    def list_stock_picking(self):
        return {}

    def select(self):
        return {"picking_id": {"coerce": to_int, "required": True, "type": "integer"}}

    def scan_line(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "barcode": {"required": True, "type": "string"},
        }

    def select_line(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "package_id": {"coerce": to_int, "required": False, "type": "integer"},
            "move_line_id": {"coerce": to_int, "required": False, "type": "integer"},
        }

    def reset_line_qty(self):
        return {"move_line_id": {"coerce": to_int, "required": True, "type": "integer"}}

    def set_line_qty(self):
        return {"move_line_id": {"coerce": to_int, "required": True, "type": "integer"}}

    def scan_pack_action(self):
        return {
            "move_line_ids": {
                "type": "list",
                "required": True,
                "schema": {"coerce": to_int, "required": True, "type": "integer"},
            },
            "barcode": {"required": True, "type": "string"},
        }

    def set_custom_qty(self):
        return {
            "move_line_id": {"coerce": to_int, "required": True, "type": "integer"},
            "qty_done": {"coerce": to_float, "required": True, "type": "float"},
        }

    def new_package(self):
        return {
            "move_line_ids": {
                "type": "list",
                "required": True,
                "schema": {"coerce": to_int, "required": True, "type": "integer"},
            }
        }


class ShopfloorCheckoutValidatorResponse(Component):
    """Validators for the Checkout endpoints responses"""

    _inherit = "base.shopfloor.validator.response"
    _name = "shopfloor.checkout.validator.response"
    _usage = "checkout.validator.response"

    _start_state = "select_document"

    def _states(self):
        """List of possible next states

        With the schema of the data send to the client to transition
        to the next state.
        """
        # TODO schemas
        return {
            "select_document": {},
            "manual_selection": {},
            "select_line": {},
            "select_pack": {},
            "change_quantity": {},
            "select_dest_package": {},
            "summary": {},
            "change_package_type": {},
            "confirm_done": {},
        }

    def scan_document(self):
        return self._response_schema(next_states={"select_document", "select_line"})

    def list_stock_picking(self):
        return self._response_schema(next_states={"manual_selection"})

    def select(self):
        return self._response_schema(
            next_states={"manual_selection", "summary", "select_line"}
        )

    def scan_line(self):
        return self._response_schema(next_states={"select_line", "select_pack"})

    def select_line(self):
        return self.scan_line()

    def reset_line_qty(self):
        return self._response_schema(next_states={"select_pack"})

    def set_line_qty(self):
        return self._response_schema(next_states={"select_pack"})

    def scan_pack_action(self):
        return self._response_schema(
            next_states={"select_pack", "select_line", "summary"}
        )

    def set_custom_qty(self):
        return self._response_schema(next_states={"select_pack"})

    def new_package(self):
        return self._response_schema(next_states={"select_line"})
