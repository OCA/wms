# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)


from datetime import datetime

from freezegun import freeze_time

from .common import Common


class TestSaleLineAvailablilityStatus(Common):
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
        self.assertEqual(self.line.delayed_qty, 0.0)

    def test_available_full(self):
        self._set_stock(self.product, 100)
        self.sale.action_confirm()
        self.assertEqual(self.line.availability_status, "full")
        self.assertEqual(self.line.delayed_qty, 0.0)

    def test_available_partial(self):
        self._set_stock(self.product, 50)
        self.sale.action_confirm()
        self.assertEqual(self.line.availability_status, "partial")
        self.assertEqual(self.line.available_qty, 50.0)
        self.assertEqual(self.line.delayed_qty, 50.0)

    @freeze_time("2021-07-01 12:00:00")
    def test_available_restock(self):
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
        self.assertEqual(self.line.available_qty, 0.0)
        self.assertEqual(self.line.delayed_qty, 0.0)
