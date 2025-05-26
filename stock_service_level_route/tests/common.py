# Copyright 2024 Foodles (https://www.foodles.co)
# @author Pierre Verkest <pierreverkest84@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import fields
from odoo.tests.common import TransactionCase


class StockServiceLeveLCommonCase(TransactionCase):
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
        cls.pick_ship_route = cls.env["stock.route"].search(
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
        location_id = location.id if location else self.warehouse.lot_stock_id.id

        # Créer ou récupérer le quant pour le produit et l'emplacement
        quant = self.env["stock.quant"].search(
            [
                ("product_id", "=", self.product.id),
                ("location_id", "=", location_id),
            ],
            limit=1,
        )

        # Si aucun quant n'existe, on le crée
        if not quant:
            quant = self.env["stock.quant"].create(
                {
                    "product_id": self.product.id,
                    "location_id": location_id,
                    "quantity": 0.0,  # Initialiser à 0 si non existant
                }
            )

        # Appliquer la nouvelle quantité comptée
        quant.inventory_quantity = qty
        quant.inventory_date = fields.Date.today()
        quant.user_id = self.env.user.id

        # Appliquer l'ajustement de l'inventaire
        quant.action_apply_inventory()
