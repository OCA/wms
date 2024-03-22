# Copyright 2024 Foodles (https://www.foodles.co)
# @author Pierre Verkest <pierreverkest84@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from .common import StockServiceLeveLCommonCase


class TestStockServiceLevel(StockServiceLeveLCommonCase):
    def test_stock_service_level_name_get(self):
        self.assertEqual(self.service_level_std.name_get()[0][1], "[STD] standard")
        self.assertEqual(self.service_level_premium.name_get()[0][1], "[PRM] premium")

    def _update_product_stock(self, qty, location=None):
        inventory = self.env["stock.inventory"].create(
            {
                "name": "Test Inventory",
                "product_ids": [(6, 0, self.product.ids)],
                "state": "confirm",
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_qty": qty,
                            "location_id": location.id
                            if location
                            else self.warehouse.lot_stock_id.id,
                            "product_id": self.product.id,
                            "product_uom_id": self.product.uom_id.id,
                        },
                    )
                ],
            }
        )
        inventory.action_validate()

    def test_procurement_with_2_steps_output(self):

        procurement_group = self.env["procurement.group"].create(
            {"name": "My procurement", "move_type": "one"}
        )
        self.env["procurement.group"].run(
            [
                self.env["procurement.group"].Procurement(
                    self.product,
                    15,
                    self.product.uom_id,
                    self.customer_loc,
                    "a name",
                    "an origin standard service level",
                    self.env.company,
                    {
                        "group_id": procurement_group,
                        "service_level_id": self.service_level_std.id,
                    },
                ),
                self.env["procurement.group"].Procurement(
                    self.product,
                    30,
                    self.product.uom_id,
                    self.customer_loc,
                    "a name",
                    "an origin premium service level",
                    self.env.company,
                    {
                        "group_id": procurement_group,
                        "service_level_id": self.service_level_premium.id,
                    },
                ),
            ]
        )

        def assert_move_qty_per_service_level(
            moves, expected_service_level, expect_qty
        ):
            concern_move = moves.filtered(
                lambda mov: mov.service_level_id == expected_service_level
            )
            self.assertEqual(len(concern_move), 1)
            self.assertEqual(concern_move.product_uom_qty, expect_qty)

        pickings = self.env["stock.picking"].search(
            [("group_id", "=", procurement_group.id)]
        )
        self.assertEqual(len(pickings), 2)
        delivery = pickings.filtered(
            lambda pick: pick.picking_type_id.code == "outgoing"
        )
        pick = pickings.filtered(lambda pick: pick.picking_type_id.code == "internal")

        self.assertEqual(delivery.state, "waiting")
        self.assertEqual(len(delivery.move_ids_without_package), 2)
        assert_move_qty_per_service_level(
            delivery.move_ids_without_package, self.service_level_std, 15
        )
        assert_move_qty_per_service_level(
            delivery.move_ids_without_package, self.service_level_premium, 30
        )

        self.assertEqual(pick.state, "confirmed")
        self.assertEqual(len(delivery.move_ids_without_package), 2)
        assert_move_qty_per_service_level(
            pick.move_ids_without_package, self.service_level_std, 15
        )
        assert_move_qty_per_service_level(
            pick.move_ids_without_package, self.service_level_premium, 30
        )
