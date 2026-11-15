# Copyright 2026 ACSONE SA/NV
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
        cls.customers = cls.env.ref("stock.stock_location_customers")
        cls.picking_type = cls.menu.sudo().picking_type_ids
        cls.wh = cls.picking_type.warehouse_id
        cls.wh.delivery_steps = "pick_ship"
        cls.out = cls.wh.wh_output_stock_loc_id
        cls.stock = cls.wh.lot_stock_id
        cls.StockLocation = cls.StockLocation.sudo()
        cls.move_obj = cls.env["stock.move"]
        cls.StockLocation._parent_store_compute()
        cls.loc_lvl = cls.wh.lot_stock_id
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

        cls.out_1 = cls.StockLocation.create(
            {"name": "OUT-1", "barcode": "OUT-1", "location_id": cls.out.id}
        )

        # products
        Product = cls.env["product.product"].sudo()
        cls.uom_unit = cls.env.ref("uom.product_uom_unit")
        cls.product_1 = Product.create(
            {"name": "Wood", "type": "product", "uom_id": cls.uom_unit.id}
        )
        cls.product_2 = Product.create(
            {"name": "Stone", "type": "product", "uom_id": cls.uom_unit.id}
        )
        cls.product_1.route_ids |= cls.wh.delivery_route_id
        cls.product_2.route_ids |= cls.wh.delivery_route_id

        cls.release_channel_1 = (
            cls.env["stock.release.channel"].sudo().create({"name": "Channel Test 1"})
        )
        cls.release_channel_2 = (
            cls.env["stock.release.channel"].sudo().create({"name": "Channel Test 2"})
        )

        cls.out.release_channel_restriction = "same"

    def setUp(self):
        super().setUp()
        self.service = self.get_service(
            "location_content_transfer", menu=self.menu, profile=self.profile
        )
        self.stock_action = self.service._actions_for("stock")

    def test_set_destination(self):
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

        values = {
            "warehouse_id": self.wh,
        }

        self.env["procurement.group"].run(
            [
                self.env["procurement.group"].Procurement(
                    self.product_1,
                    5.0,
                    self.product_1.uom_id,
                    self.customers,
                    self.product_1.display_name,
                    self.product_1.display_name,
                    self.env.company,
                    values,
                )
            ]
        )

        ship_move = self.env["stock.move"].search(
            [
                ("location_dest_id", "=", self.customers.id),
                ("product_id", "=", self.product_1.id),
            ]
        )
        ship_move.picking_id.release_channel_id = self.release_channel_1

        pick_move = self.env["stock.move"].search(
            [
                ("location_id", "=", self.stock.id),
                ("product_id", "=", self.product_1.id),
            ]
        )

        pick_move._action_assign()

        # Assign user to move
        pick_move.move_line_ids.qty_done = 5.0
        pick_move.picking_id.user_id = self.env.user

        response = self.service.dispatch(
            "set_destination_all",
            params={
                "location_id": self.loc_lvl_1_1_2.id,
                "barcode": self.out_1.barcode,
            },
        )

        self.assertEqual(pick_move.location_dest_id, self.out_1)
        self.assertEqual(
            self.out_1.current_release_channel_restriction_id, self.release_channel_1
        )

        self.env["procurement.group"].run(
            [
                self.env["procurement.group"].Procurement(
                    self.product_2,
                    5.0,
                    self.product_2.uom_id,
                    self.customers,
                    self.product_2.display_name,
                    self.product_2.display_name,
                    self.env.company,
                    values,
                )
            ]
        )

        ship_move = self.env["stock.move"].search(
            [
                ("location_dest_id", "=", self.customers.id),
                ("product_id", "=", self.product_2.id),
            ]
        )
        ship_move.picking_id.release_channel_id = self.release_channel_2

        pick_move = self.env["stock.move"].search(
            [
                ("location_id", "=", self.stock.id),
                ("product_id", "=", self.product_2.id),
            ]
        )

        pick_move._action_assign()

        pick_move.move_line_ids.qty_done = 5.0
        pick_move.picking_id.user_id = self.env.user

        response = self.service.dispatch(
            "set_destination_all",
            params={
                "location_id": self.loc_lvl_1_1_1.id,
                "barcode": self.out_1.barcode,
            },
        )

        self.assertEqual(
            "You cannot place it here", response.get("message").get("body")
        )
