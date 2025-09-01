# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.addons.shopfloor_base.tests.common import CommonCase


class TestStockLocation(CommonCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.StockLocation = cls.env["stock.location"]

        cls.menu = cls.env.ref(
            "shopfloor.shopfloor_menu_demo_location_content_transfer"
        )
        cls.profile = cls.env.ref("shopfloor_base.profile_demo_1")
        cls.picking_type = cls.menu.sudo().picking_type_ids
        cls.wh = cls.picking_type.warehouse_id
        cls.StockLocation = cls.StockLocation.sudo()
        cls.move_obj = cls.env["stock.move"]
        cls.StockLocation._parent_store_compute()
        cls.loc_lvl = cls.env.ref("stock.stock_location_locations")
        cls.loc_lvl_1 = cls.StockLocation.create(
            {"name": "level_1", "location_id": cls.loc_lvl.id}
        )
        cls.loc_lvl_1_1 = cls.StockLocation.create(
            {"name": "level_1_1", "location_id": cls.loc_lvl_1.id}
        )

        cls.loc_lvl_1_1_1 = cls.StockLocation.create(
            {"name": "level_1_1_1", "location_id": cls.loc_lvl_1_1.id}
        )
        cls.loc_lvl_1_1_2 = cls.StockLocation.create(
            {"name": "level_1_1_1", "location_id": cls.loc_lvl_1_1.id}
        )
        cls.default_product_restriction = "any"

        # products
        Product = cls.env["product.product"].sudo()
        cls.uom_unit = cls.env.ref("uom.product_uom_unit")
        cls.product_1 = Product.create(
            {"name": "Wood", "type": "product", "uom_id": cls.uom_unit.id}
        )
        cls.product_2 = Product.create(
            {"name": "Stone", "type": "product", "uom_id": cls.uom_unit.id}
        )

        # # quants
        # StockQuant = cls.env["stock.quant"].sudo()
        # cls.quant_1_lvl_1_1_1 = StockQuant.create(
        #     {
        #         "product_id": cls.product_1.id,
        #         "location_id": cls.loc_lvl_1_1_1.id,
        #         "quantity": 10.0,
        #         "owner_id": cls.env.user.id,
        #     }
        # )
        # cls.quant_2_lvl_1_1_1 = StockQuant.create(
        #     {
        #         "product_id": cls.product_2.id,
        #         "location_id": cls.loc_lvl_1_1_1.id,
        #         "quantity": 10.0,
        #         "owner_id": cls.env.user.id,
        #     }
        # )
        # cls.quant_1_lvl_1_1_2 = StockQuant.create(
        #     {
        #         "product_id": cls.product_1.id,
        #         "location_id": cls.loc_lvl_1_1_2.id,
        #         "quantity": 10.0,
        #         "owner_id": cls.env.user.id,
        #     }
        # )
        # cls.quant_2_lvl_1_1_2 = StockQuant.create(
        #     {
        #         "product_id": cls.product_2.id,
        #         "location_id": cls.loc_lvl_1_1_2.id,
        #         "quantity": 10.0,
        #         "owner_id": cls.env.user.id,
        #     }
        # )

    def setUp(self):
        super().setUp()
        self.service = self.get_service(
            "location_content_transfer", menu=self.menu, profile=self.profile
        )
        self.stock_action = self.service._actions_for("stock")

    def test_set_destination(self):
        # Put product 1 in location 1-1-2
        # Put product 2 in location 1-1-1

        # Enable restriction on 1-1-2
        # Try to transfer location 1-1-1 to 1-1-2
        manager = (
            self.env["res.users"]
            .sudo()
            .create({"name": "Manager", "login": "stock_manager"})
        )
        manager.groups_id |= self.env.ref("stock.group_stock_manager")
        self.env.user.groups_id |= self.env.ref("stock.group_stock_user")
        self.env["stock.quant"].with_user(manager).with_context(
            inventory_mode=True
        ).create(
            {
                "product_id": self.product_2.id,
                "inventory_quantity": 10.0,
                "location_id": self.loc_lvl_1_1_1.id,
            }
        )._apply_inventory()
        self.env["stock.quant"].with_user(manager).with_context(
            inventory_mode=True
        ).create(
            {
                "product_id": self.product_1.id,
                "inventory_quantity": 10.0,
                "location_id": self.loc_lvl_1_1_2.id,
            }
        )._apply_inventory()
        self.loc_lvl_1_1_2.barcode = "LVL_1_1_2"
        self.loc_lvl_1_1_1.barcode = "LVL_1_1_1"
        self.move = self.move_obj.create(
            {
                "name": "Level 1-1-1 -> Level 1-1-2",
                "location_id": self.loc_lvl_1_1_2.id,
                "location_dest_id": self.loc_lvl_1_1_1.id,
                "product_id": self.product_1.id,
                "product_uom": self.product_1.uom_id.id,
                "product_uom_qty": 5.0,
                "picking_type_id": self.env.ref("stock.picking_type_internal").id,
            }
        )

        self.move._action_confirm()
        self.move._action_assign()
        self.move._assign_picking()

        # Assign user to move
        self.move.move_line_ids.qty_done = 5.0
        self.move.picking_id.user_id = self.env.user

        self.loc_lvl_1_1_1.product_restriction = "same"
        response = self.service.dispatch(
            "set_destination_all",
            params={
                "location_id": self.loc_lvl_1_1_2.id,
                "barcode": self.loc_lvl_1_1_1.barcode,
            },
        )

        self.assertEqual(
            "You cannot place it here", response.get("message").get("body")
        )
        self.loc_lvl_1_1_1.product_restriction = "any"
        self.loc_lvl_1_1_1.invalidate_recordset()
        response = self.service.dispatch(
            "set_destination_all",
            params={
                "location_id": self.loc_lvl_1_1_2.id,
                "barcode": self.loc_lvl_1_1_1.barcode,
            },
        )

        self.assertEqual("scan_location", response.get("next_state"))
