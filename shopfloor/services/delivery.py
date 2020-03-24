from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import Component


class Delivery(Component):
    """
    Methods for the Delivery Process

    Deliver the goods by processing the PACK and raw products by delivery order.
    Last step in the pick/pack/ship steps. (Cluster Picking → Checkout → Delivery)

    Multiple operators could be processing a same delivery order.

    Expected:

    * Existing packages are moved to customer location
    * Products are moved to customer location as raw products
    * Bin packed products are placed in new shipping package and shipped to customer

    Flow Diagram: https://www.draw.io/#G1qRenBcezk50ggIazDuu2qOfkTsoIAxXP
    """

    _inherit = "base.shopfloor.service"
    _name = "shopfloor.delivery"
    _usage = "delivery"
    _description = __doc__

    # TODO we don't know yet if we have to select a destination package or a
    # destination location
    def xxx(self, barcode):
        return self._result()

    # TODO we'll probably to add the selected destination package or location
    # id in every endpoint parameters and returns
    def scan_stock_picking(self, barcode):
        """Scan a stock picking or a package

        When a package is scanned, and has an available move line part of the
        expected picking type, the package level is directly set to "done" and
        the stock picking of the line is returned to work on its other lines.

        When a stock picking is scanned and is partially or fully available, it
        is returned to work on its lines.

        When all the available move lines and package levels of the stock picking
        are done, the user is directed to the summary screen.

        Transitions:
        * select_source: error when scanning (stock picking not available, ...)
        * move_set_done: when a valid package or stock picking has been scanned
          and the stock picking still have lines / package levels not done
        * summary: when a valid package or stock picking has been scanned
          and all the lines of the stock picking are done
        """
        return self._response()

    def list_stock_picking(self):
        """Return the list of stock pickings for the picking type

        It returns only stock picking available or partially available.

        Transitions:
        * manual_selection: next state to show the list of stock pickings
        """
        return self._response()

    def select(self, picking_id):
        """Select a stock picking from its ID (found using /list_stock_picking)

        It returns only stock picking available or partially available.

        Transitions:
        * manual_selection: the selected stock picking is no longer valid
        * move_set_done: the selected stock picking has lines not done
        * summary: the selected stock picking has all lines done
        """
        return self._response()

    def set_qty_done_pack(self, picking_id, package_id):
        """Set a package to "Done"

        Transitions:
        * move_set_done: error when setting done, or success but the stock
        picking has other lines to set done
        * summary: all the lines of the stock picking are now done
        """
        return self._response()

    def set_qty_done_line(self, picking_id, line_id):
        """Set a move line to "Done"

        Should be called only for lines of raw products, /set_qty_done_pack
        must be used for lines that move a package.

        Transitions:
        * move_set_done: error when setting done, or success but the stock
        picking has other lines to set done
        * summary: all the lines of the stock picking are now done
        """
        return self._response()

    def scan_line(self, picking_id, barcode):
        """Set a move line or package to "Done" from a barcode

        If the barcode is a package in the picking and is available, it
        sets it to done.

        If the barcode is a product or a product's packaging, the move lines
        for this product are set to done. However, if the product is in more
        than one package, a package barcode is requested, and if the product is
        tracked by lot/serial, a lot is asked.

        If the barcode is a lot, the mbarcode ove lines for this lot are set to
        done. However, if the lot is in more than one package, a package
        barcode is requested.

        NOTE: see scan_line in the Checkout service.

        Transitions:
        * move_set_done: error when setting done, or success but the stock
        picking has other lines to set done
        * summary: all the lines of the stock picking are now done
        """
        return self._response()

    def summary(self, picking_id):
        """Return data for the summary screen

        Transitions:
        * summary
        """
        return self._response()

    def reset_qty_done_pack(self, picking_id, package_id):
        """Remove "Done" on a package

        Transitions:
        * summary: return back to this state
        """
        return self._response()

    def reset_qty_done_line(self, picking_id, line_id):
        """Remove "Done" on a move line

        Should be called only for lines of raw products, /set_qty_done_pack
        must be used for lines that move a package.

        Transitions:
        * summary: return back to this state
        """
        return self._response()

    def done(self, picking_id):
        """Set the stock picking to done

        Transitions:
        * summary: error during action
        * select_source: stock picking was set to done, user can work on the
          next stock picking
        """
        return self._response()

    def back_to_move_set_done(self, picking_id):
        """Allow to return to the "move_set_done" state with refreshed data

        Transitions:
        * move_set_done: return to this state when not all lines of the
        stock picking are done
        * summary: return back to this state when all lines are done
        """
        return self._response()


class ShopfloorDeliveryValidator(Component):
    """Validators for the Delivery endpoints"""

    _inherit = "base.shopfloor.validator"
    _name = "shopfloor.delivery.validator"
    _usage = "delivery.validator"

    # TODO
    def xxx(self):
        return {}

    def scan_stock_picking(self):
        return {"barcode": {"required": True, "type": "string"}}

    def list_stock_picking(self):
        return {}

    def select(self):
        return {"picking_id": {"coerce": to_int, "required": True, "type": "integer"}}

    def set_qty_done_pack(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "package_id": {"coerce": to_int, "required": True, "type": "integer"},
        }

    def set_qty_done_line(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "move_line_id": {"coerce": to_int, "required": True, "type": "integer"},
        }

    def scan_line(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "barcode": {"required": True, "type": "string"},
        }

    def summary(self):
        return {"picking_id": {"coerce": to_int, "required": True, "type": "integer"}}

    def reset_qty_done_pack(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "package_id": {"coerce": to_int, "required": True, "type": "integer"},
        }

    def reset_qty_done_line(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "move_line_id": {"coerce": to_int, "required": True, "type": "integer"},
        }

    def done(self):
        return {"picking_id": {"coerce": to_int, "required": True, "type": "integer"}}

    def back_to_move_set_done(self):
        return {"picking_id": {"coerce": to_int, "required": True, "type": "integer"}}


class ShopfloorDeliveryValidatorResponse(Component):
    """Validators for the Delivery endpoints responses"""

    _inherit = "base.shopfloor.validator.response"
    _name = "shopfloor.delivery.validator.response"
    _usage = "delivery.validator.response"

    _start_state = "start"

    def _states(self):
        """List of possible next states

        With the schema of the data send to the client to transition
        to the next state.
        """
        return {
            "start": {},
            "select_source": self._schema_select_source,
            "manual_selection": self._schema_selection_list,
            "move_set_done": self._schema_stock_picking_details,
            "summary": self._schema_stock_picking_details,
            "confirm_summary": self._schema_stock_picking_details,
        }

    # TODO add the selected dest. package or location in returns (to keep it stateless)
    @property
    def _schema_stock_picking_details(self):
        schema = self.schemas().picking()
        schema.update(
            {
                "move_lines": {
                    "type": "list",
                    "schema": {"type": "dict", "schema": self.schemas().move_line()},
                }
            }
        )
        return {"picking": {"type": "dict", "schema": schema}}

    @property
    def _schema_selection_list(self):
        return {
            "pickings": {
                "type": "list",
                "schema": {"type": "dict", "schema": self.schemas().picking()},
            }
        }

    @property
    def _schema_select_source(self):
        # TODO we don't know yet if we want to show the dest. location or package
        return {}

    def xxx(self):
        return self._response_schema(next_states={"start", "select_source"})

    def scan_stock_picking(self):
        return self._response_schema(
            next_states={"select_source", "move_set_done", "summary"}
        )

    def list_stock_picking(self):
        return self._response_schema(next_states={"manual_selection"})

    def select(self):
        return self._response_schema(
            next_states={"manual_selection", "move_set_done", "summary"}
        )

    def set_qty_done_pack(self):
        return self._response_schema(next_states={"move_set_done", "summary"})

    def set_qty_done_line(self):
        return self._response_schema(next_states={"move_set_done", "summary"})

    def scan_line(self):
        return self._response_schema(next_states={"move_set_done", "summary"})

    def summary(self):
        return self._response_schema(next_states={"summary"})

    def reset_qty_done_pack(self):
        return self._response_schema(next_states={"summary"})

    def reset_qty_done_line(self):
        return self._response_schema(next_states={"summary"})

    def done(self):
        return self._response_schema(next_states={"confirm_summary", "start"})

    def back_to_move_set_done(self):
        return self._response_schema(next_states={"move_set_done", "summary"})
