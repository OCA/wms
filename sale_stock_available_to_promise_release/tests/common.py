# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.tests.common import SavepointCase


class Common(SavepointCase):
    at_install = False
    post_install = True

    @classmethod
    def setUpClassProduct(cls):
        cls.mto_route = cls.env.ref("stock.route_warehouse0_mto")
        cls.mto_route.active = True
        cls.uom_unit = cls.env.ref("uom.product_uom_unit")
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Storable Product",
                "uom_id": cls.uom_unit.id,
                "type": "product",
            }
        )

    @classmethod
    def setUpClassSale(cls):
        customer = cls.env["res.partner"].create(
            {"name": "Partner who loves storable products"}
        )
        cls.sale = cls.env["sale.order"].create({"partner_id": customer.id})
        cls.line = cls.env["sale.order.line"].create(
            {
                "order_id": cls.sale.id,
                "product_id": cls.product.id,
                "product_uom_qty": 100,
                "product_uom": cls.uom_unit.id,
            }
        )

    @classmethod
    def setUpClassStock(cls):
        cls.stock_location = cls.env.ref("stock.stock_location_stock")
        cls.suppliers_location = cls.env.ref("stock.stock_location_suppliers")

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.setUpClassProduct()
        cls.setUpClassSale()
        cls.setUpClassStock()

    def _set_stock(self, product, qty):
        self.env["stock.quant"]._update_available_quantity(
            product, self.stock_location, qty
        )
