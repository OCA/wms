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
        cls.parking = cls.StockLocation.sudo().create(
            {
                "name": "Parking",
                "location_id": cls.wh.view_location_id.id,
                "barcode": "L#PARK",
            }
        )
        cls.loc_lvl = cls.env.ref("stock.stock_location_locations")
        cls.loc_lvl.sudo().usage = "view"
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

        # Create Putaways
        cls.env["stock.putaway.rule"].sudo().create(
            {
                "product_id": cls.product_2.id,
                "location_in_id": cls.loc_lvl.id,
                "location_out_id": cls.loc_lvl_1_1_1.id,
            }
        )

        cls.store = (
            cls.env["stock.picking.type"]
            .sudo()
            .create(
                {
                    "name": "Parking -> Stock",
                    "sequence_code": "PARK/",
                    "default_location_dest_id": cls.loc_lvl.id,
                    "default_location_src_id": cls.parking.id,
                    "code": "internal",
                }
            )
        )
        cls.menu.sudo().write(
            {"allow_move_create": True, "move_create_is_possible": True}
        )
        cls.menu.sudo().picking_type_ids = cls.store

    def setUp(self):
        super().setUp()
        self.service = self.get_service(
            "location_content_transfer", menu=self.menu, profile=self.profile
        )
        self.stock_action = self.service._actions_for("stock")

    def test_set_destination(self):
        # Put product 2 in Parking
        # Put product 1 in product 2 putaway location
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
                "location_id": self.parking.id,
            }
        )._apply_inventory()
        self.env["stock.quant"].with_user(manager).with_context(
            inventory_mode=True
        ).create(
            {
                "product_id": self.product_1.id,
                "inventory_quantity": 10.0,
                "location_id": self.loc_lvl_1_1_1.id,
            }
        )._apply_inventory()
        self.loc_lvl_1_1_2.barcode = "LVL_1_1_2"
        self.loc_lvl_1_1_1.barcode = "LVL_1_1_1"

        response = self.service.dispatch(
            "scan_location",
            params={
                "barcode": self.parking.barcode,
            },
        )

        self.assertEqual("scan_destination_all", response.get("next_state"))

        self.loc_lvl_1_1_1.product_restriction = "same"
        response = self.service.dispatch(
            "set_destination_all",
            params={
                "location_id": self.parking.id,
                "barcode": self.loc_lvl_1_1_1.barcode,
            },
        )

        self.assertEqual(
            "You cannot place it here\nThe location level_1_1_1 "
            "contains already another product than ['Stone']",
            response.get("message").get("body"),
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

    def test_putaways(self):
        """
        In location content transfer, the moves destinations are computed at
        picking creation.

        If two products have the same destination, a proper message should
        be returned to user
        """
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
                "location_id": self.parking.id,
            }
        )._apply_inventory()
        self.env["stock.quant"].with_user(manager).with_context(
            inventory_mode=True
        ).create(
            {
                "product_id": self.product_1.id,
                "inventory_quantity": 10.0,
                "location_id": self.loc_lvl_1_1_1.id,
            }
        )._apply_inventory()
        self.loc_lvl_1_1_2.barcode = "LVL_1_1_2"
        self.loc_lvl_1_1_1.barcode = "LVL_1_1_1"

        self.loc_lvl_1_1_1.product_restriction = "same"
        response = self.service.dispatch(
            "scan_location",
            params={
                "barcode": self.parking.barcode,
            },
        )
        message = (
            "The location level_1_1_1 contains already another product than ['Stone']\n"
            + "The content of Parking cannot be transferred to Parking with this "
            "scenario for product Stone."
        )
        self.assertEqual(message, response.get("message").get("body"))
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
