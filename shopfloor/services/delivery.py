from odoo import fields
from odoo.osv import expression

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

    _inherit = "base.shopfloor.process"
    _name = "shopfloor.delivery"
    _usage = "delivery"
    _description = __doc__

    @property
    def data_struct(self):
        return self.actions_for("data")

    @property
    def msg_store(self):
        return self.actions_for("message")

    def _response_for_deliver(self, picking=None, message=None):
        """Transition to the 'deliver' state

        If no picking is passed, the screen shows an empty screen
        """
        return self._response(
            next_state="deliver",
            data={
                "picking": self._data_for_stock_picking(picking) if picking else None
            },
            message=message,
        )

    def _data_for_stock_picking(self, picking):
        data = self.data_struct.picking(picking)
        data.update(
            {
                "move_lines": [
                    self.data_struct.move_line(ml) for ml in picking.move_line_ids
                ]
            }
        )
        return data

    def scan_deliver(self, barcode, picking_id=None):
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

        The ``picking_id`` parameter is used to be stateless: if the client
        sends a wrong barcode, it allows to stay on the last picking with
        updated data (and we really want to refresh data because several
        users may work on the same transfer).

        Transitions:
        * deliver: always return here with the data for the last touched
        picking or no picking if the picking has been set to done
        """
        search = self.actions_for("search")
        picking = search.picking_from_scan(barcode)
        if picking:
            if picking.state == "done":
                return self._response_for_deliver(message=self.msg_store.already_done())
            if picking.state not in ("assigned", "partially_available"):
                return self._response_for_deliver(
                    message=self.msg_store.stock_picking_not_available(picking)
                )
            if picking.picking_type_id not in self.picking_types:
                return self._response_for_deliver(
                    message=self.msg_store.cannot_move_something_in_picking_type()
                )
            return self._response_for_deliver(picking=picking)

        # We should have only a picking_id because the client was working
        # on it already, so no need to validate the picking type
        if picking_id:
            picking = self.env["stock.picking"].browse(picking_id).exists()

        package = search.package_from_scan(barcode)
        if package:
            return self._deliver_package(picking, package)

        product = search.product_from_scan(barcode)
        if product:
            return self._deliver_product(picking, product)

        lot = search.lot_from_scan(barcode)
        if lot:
            return self._deliver_lot(picking, lot)

        return self._response_for_deliver(
            picking=picking, message=self.msg_store.barcode_not_found()
        )

    def _set_lines_done(self, lines):
        for line in lines:
            # note: the package level is automatically set to "is_done" when
            # the qty_done is full
            line.qty_done = line.product_uom_qty

    def _deliver_package(self, picking, package):
        lines = package.move_line_ids
        lines = lines.filtered(
            lambda l: l.state in ("assigned", "partially_available")
            and l.picking_id.picking_type_id in self.picking_types
        )
        if not lines:
            # TODO tests
            return self._response_for_deliver(
                picking=picking,
                message=self.msg_store.cannot_move_something_in_picking_type(),
            )
        # TODO add a message if any of the lines already had a qty_done > 0
        self._set_lines_done(lines)
        new_picking = fields.first(lines.mapped("picking_id"))
        return self._response_for_deliver(picking=new_picking)

    def _lines_base_domain(self):
        return [
            # we added auto_join for this, otherwise, the ORM would search all pickings
            # in the picking type, and then use IN (ids)
            ("picking_id.picking_type_id", "in", self.picking_types.ids),
            ("qty_done", "=", 0),
        ]

    def _lines_from_lot_domain(self, product):
        return expression.AND(
            [self._lines_base_domain(), [("lot_id", "=", product.id)]]
        )

    def _lines_from_product_domain(self, product):
        return expression.AND(
            [self._lines_base_domain(), [("product_id", "=", product.id)]]
        )

    def _deliver_product(self, picking, product):
        if product.tracking in ("lot", "serial"):
            # TODO test
            return self._response_for_deliver(
                picking, message=self.msg_store.scan_lot_on_product_tracked_by_lot()
            )

        lines = self.env["stock.move.line"].search(
            self._lines_from_product_domain(product)
        )
        if not lines:
            # TODO not found
            pass

        new_picking = fields.first(lines.mapped("picking_id"))
        # When products are as units outside of packages, we can select them for
        # packing, but if they are in a package, we want the user to scan the packages.
        # If the product is only in one package though, scanning the product selects
        # the package.
        packages = lines.mapped("package_id")
        # Do not use mapped here: we want to see if we have more than one package,
        # but also if we have one product as a package and the same product as
        # a unit in another line. In both cases, we want the user to scan the
        # package.
        if packages and len({l.package_id for l in lines}) > 1:
            return self._response_for_deliver(
                new_picking,
                message=self.msg_store.product_multiple_packages_scan_package(),
            )
        elif packages:
            # we have 1 package
            # TODO if the package contain more than one product, set them to moved
            # as well or forbid it (maybe could be done in _set_lines_done)
            pass
        self._set_lines_done(lines)
        return self._response_for_deliver(new_picking)

    def _deliver_lot(self, picking, lot):
        lines = self.env["stock.move.line"].search(self._lines_from_lot_domain(lot))
        if not lines:
            # TODO not found
            pass

        new_picking = fields.first(lines.mapped("picking_id"))

        # When lots are as units outside of packages, we can select them for
        # packing, but if they are in a package, we want the user to scan the packages.
        # If the product is only in one package though, scanning the lot selects
        # the package.
        packages = lines.mapped("package_id")
        # Do not use mapped here: we want to see if we have more than one
        # package, but also if we have one lot as a package and the same lot as
        # a unit in another line. In both cases, we want the user to scan the
        # package.
        if packages and len({l.package_id for l in lines}) > 1:
            return self._response_for_deliver(
                new_picking, message=self.msg_store.lot_multiple_packages_scan_package()
            )
        elif packages:
            # we have 1 package
            # TODO if the package contain more than one product, set them to moved
            # as well or forbid it (maybe could be done in _set_lines_done)
            pass

        self._set_lines_done(lines)
        return self._response_for_deliver(new_picking)

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
        return {
            "barcode": {"required": True, "type": "string"},
            "picking_id": {
                "coerce": to_int,
                "required": False,
                "nullable": True,
                "type": "integer",
            },
        }

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
        schema = self.schemas.picking()
        schema.update(
            {
                "move_lines": {
                    "type": "list",
                    "schema": {"type": "dict", "schema": self.schemas.move_line()},
                }
            }
        )
        return {"picking": {"type": "dict", "nullable": True, "schema": schema}}

    @property
    def _schema_selection_list(self):
        return {
            "pickings": {
                "type": "list",
                "schema": {"type": "dict", "schema": self.schemas.picking()},
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
