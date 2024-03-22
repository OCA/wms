# Copyright 2024 Foodles (https://www.foodles.co)
# @author Pierre Verkest <pierreverkest84@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.tests.common import SavepointCase


class StockServiceLeveLCommonCase(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.service_level_std = cls.env["stock.service.level"].create(
            {
                "name": "standard",
                "code": "STD",
            }
        )
        cls.service_level_premium = cls.env["stock.service.level"].create(
            {
                "name": "premium",
                "code": "PRM",
            }
        )
        cls.customer_loc = cls.env.ref("stock.stock_location_customers")
        cls.output_loc = cls.env.ref("stock.stock_location_output")
        cls.product = cls.env.ref("product.product_product_16")
        cls.warehouse = cls.env.ref("stock.warehouse0")
        cls.warehouse.write({"delivery_steps": "pick_ship"})
        cls.env["res.config.settings"].write(
            {
                "group_stock_adv_location": True,
                "group_stock_multi_locations": True,
            }
        )
        cls.pick_ship_route = cls.env["stock.location.route"].search(
            [("name", "ilike", "deliver in 2")]
        )
        cls.product.categ_id.route_ids |= cls.pick_ship_route
        cls.location_1 = cls.env["stock.location"].create(
            {"name": "loc1", "location_id": cls.warehouse.lot_stock_id.id}
        )
        cls.location_2 = cls.env["stock.location"].create(
            {"name": "loc2", "location_id": cls.warehouse.lot_stock_id.id}
        )

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
