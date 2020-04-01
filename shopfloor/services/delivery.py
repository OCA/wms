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

    Every time a package, product or lot is scanned, the package level and move line
    are set to done. When the last line is scanned, the transfer is set to done.
    Data for the last transfer for which we have been scanning a line if it is not done.
    When a transfer is scanned, it returns its data to be shown on the screen.

    Flow Diagram: https://www.draw.io/#G1qRenBcezk50ggIazDuu2qOfkTsoIAxXP
    """

    _inherit = "base.shopfloor.service"
    _name = "shopfloor.delivery"
    _usage = "delivery"
    _description = __doc__

    def scan_deliver(self, barcode):
        """Scan a stock picking or a package/product/lot

        When a stock picking is scanned and is partially or fully available, it
        is returned to show its lines.

        When a package is scanned, and has an available move line part of the
        expected picking type, the package level is directly set to "done" and
        the stock picking of the line is returned to work on its other lines.

        If the barcode is a product or a product's packaging, the move lines
        for this product are set to done. However, if the product is in more
        than one package, a package barcode is requested, and if the product is
        tracked by lot/serial, a lot is asked.

        If the barcode is a lot, the mbarcode ove lines for this lot are set to
        done. However, if the lot is in more than one package, a package
        barcode is requested.

        NOTE: see scan_line in the Checkout service.

        When all the available move lines of the stock picking are done, the
        stock picking is set to done.

        Transitions:
        * deliver: always return here with the data for the last touched picking
        or no picking if the picking has been set to done
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
        * deliver: with information about the stock.picking
        """
        return self._response()

    def set_qty_done_pack(self, picking_id, package_id):
        """Set a package to "Done"

        When all the available move lines of the stock picking are done, the
        stock picking is set to done.

        Transitions:
        * deliver: always return here with updated data
        """
        return self._response()

    def set_qty_done_line(self, picking_id, line_id):
        """Set a move line to "Done"

        Should be called only for lines of raw products, /set_qty_done_pack
        must be used for lines that move a package.

        When all the available move lines of the stock picking are done, the
        stock picking is set to done.

        Transitions:
        * deliver: always return here with updated data
        """
        return self._response()

    def reset_qty_done_pack(self, picking_id, package_id):
        """Remove "Done" on a package

        Transitions:
        * deliver: always return here with updated data
        """
        return self._response()

    def reset_qty_done_line(self, picking_id, line_id):
        """Remove "Done" on a move line

        Should be called only for lines of raw products, /set_qty_done_pack
        must be used for lines that move a package.

        Transitions:
        * deliver: always return here with updated data
        """
        return self._response()

    def done(self, picking_id):
        """Set the stock picking to done

        Transitions:
        * deliver: error during action
        * confirm_done: when not all lines of the stock.picking are done
        """
        return self._response()


class ShopfloorDeliveryValidator(Component):
    """Validators for the Delivery endpoints"""

    _inherit = "base.shopfloor.validator"
    _name = "shopfloor.delivery.validator"
    _usage = "delivery.validator"

    def scan_deliver(self):
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


class ShopfloorDeliveryValidatorResponse(Component):
    """Validators for the Delivery endpoints responses"""

    _inherit = "base.shopfloor.validator.response"
    _name = "shopfloor.delivery.validator.response"
    _usage = "delivery.validator.response"

    _start_state = "deliver"

    def _states(self):
        """List of possible next states

        With the schema of the data send to the client to transition
        to the next state.
        """
        return {
            "deliver": self._schema_deliver,
            "manual_selection": self._schema_selection_list,
            "confirm_done": self._schema_deliver,
        }

    @property
    def _schema_deliver(self):
        schema = self.schemas().picking()
        schema.update(
            {
                "move_lines": {
                    "type": "list",
                    "schema": {"type": "dict", "schema": self.schemas().move_line()},
                }
            }
        )
        return {"picking": {"type": "dict", "required": False, "schema": schema}}

    @property
    def _schema_selection_list(self):
        return {
            "pickings": {
                "type": "list",
                "schema": {"type": "dict", "schema": self.schemas().picking()},
            }
        }

    def scan_deliver(self):
        return self._response_schema(next_states={"deliver"})

    def list_stock_picking(self):
        return self._response_schema(next_states={"manual_selection"})

    def select(self):
        return self._response_schema(next_states={"deliver"})

    def set_qty_done_pack(self):
        return self._response_schema(next_states={"deliver"})

    def set_qty_done_line(self):
        return self._response_schema(next_states={"deliver"})

    def reset_qty_done_pack(self):
        return self._response_schema(next_states={"deliver"})

    def reset_qty_done_line(self):
        return self._response_schema(next_states={"deliver"})

    def done(self):
        return self._response_schema(next_states={"deliver", "confirm_done"})
