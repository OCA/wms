# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)


from datetime import datetime

from freezegun import freeze_time

from odoo.tests.common import SavepointCase


class TestSaleLineAvailablilityStatus(SavepointCase):
    at_install = False
    post_install = True

    @classmethod
    def setUpClassProduct(cls):
        cls.mto_route = cls.env.ref("stock.route_warehouse0_mto")
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
        super(TestSaleLineAvailablilityStatus, cls).setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.setUpClassProduct()
        cls.setUpClassSale()
        cls.setUpClassStock()

    def _set_stock(self, product, qty):
        self.env["stock.quant"]._update_available_quantity(
            product, self.stock_location, qty
        )

    @freeze_time("2021-07-03 12:00:00")
    def _create_replenishment_picking(self, product, qty):
        picking_type_in = self.env.ref("stock.picking_type_in")
        return self.env["stock.picking"].create(
            {
                "name": "A picking full of moves",
                "picking_type_id": picking_type_in.id,
                "location_id": self.suppliers_location.id,
                "location_dest_id": self.stock_location.id,
                "move_lines": [
                    (
                        0,
                        0,
                        {
                            "product_id": product.id,
                            "name": "A move full of storable products",
                            "picking_type_id": picking_type_in.id,
                            "location_id": self.suppliers_location.id,
                            "location_dest_id": self.stock_location.id,
                            "product_uom_qty": qty,
                            "product_uom": self.uom_unit.id,
                        },
                    )
                ],
            }
        )

    def test_available_mto(self):
        # No matter the ordered qty, if mto route is defined on the product,
        # availability_status = "mto"
        self.sale.action_confirm()
        self.assertNotEqual(self.line.availability_status, "on_order")
        self.product.route_ids = [(4, self.mto_route.id, 0)]
        self.assertEqual(self.line.availability_status, "on_order")

    def test_available_full(self):
        self._set_stock(self.product, 100)
        self.sale.action_confirm()
        self.assertEqual(self.line.availability_status, "full")

    def test_available_partial(self):
        self._set_stock(self.product, 50)
        self.sale.action_confirm()
        self.assertEqual(self.line.availability_status, "partial")
        self.assertEqual(self.line.available_qty, 50.0)

    @freeze_time("2021-07-01 12:00:00")
    def test_availabile_restock(self):
        replenishment_picking = self._create_replenishment_picking(self.product, 100)
        self.sale.action_confirm()
        self.assertEqual(self.line.availability_status, "restock")
        replenishment_picking.action_confirm()
        self.assertNotEqual(self.line.availability_status, "full")
        self.assertEqual(
            self.line.expected_availability_date, datetime(2021, 7, 3, 12, 0, 0)
        )

    def test_not_available(self):
        self.sale.action_confirm()
        self.assertEqual(
            self.line.with_context(not_available=True).availability_status, "no"
        )
