# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo.tests import TransactionCase


class TestStorageType(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.location_sequence_pallet = cls.env.ref(
            "stock_storage_type.stock_package_storage_location_pallets"
        )

        cls.stock_location = cls.env.ref("stock.stock_location_stock")
        cls.pallets_location_storage_type = cls.env.ref(
            "stock_storage_type.location_storage_type_pallets"
        )
        cls.pallets_uk_location_storage_type = cls.env.ref(
            "stock_storage_type.location_storage_type_pallets_uk"
        )
        cls.cardboxes_location_storage_type = cls.env.ref(
            "stock_storage_type.location_storage_type_cardboxes"
        )
        cls.cardboxes_stock = cls.env.ref("stock_storage_type.stock_location_cardboxes")
        cls.cardboxes_bin_1 = cls.env.ref(
            "stock_storage_type.stock_location_cardboxes_bin_1"
        )
        cls.cardboxes_bin_2 = cls.env.ref(
            "stock_storage_type.stock_location_cardboxes_bin_2"
        )
        cls.cardboxes_bin_3 = cls.env.ref(
            "stock_storage_type.stock_location_cardboxes_bin_3"
        )
        cls.cardboxes_bin_4 = cls.env.ref(
            "stock_storage_type.stock_location_cardboxes_bin_4"
        )

    def test_location_allowed_storage_types(self):
        # As cardboxes location storage type is defined on parent stock
        #  location_storage_type_ids
        self.assertEqual(
            self.cardboxes_stock.computed_storage_category_id.capacity_ids,
            self.cardboxes_location_storage_type,
        )
        # It is what's allowed on the parent stock
        self.assertEqual(
            self.cardboxes_stock.computed_storage_category_id.capacity_ids,
            self.cardboxes_location_storage_type,
        )
        # and also what's allowed on the children
        self.assertEqual(
            self.cardboxes_bin_1.computed_storage_category_id.capacity_ids,
            self.cardboxes_location_storage_type,
        )
        self.assertEqual(
            self.cardboxes_bin_2.computed_storage_category_id.capacity_ids,
            self.cardboxes_location_storage_type,
        )
        self.assertEqual(
            self.cardboxes_bin_3.computed_storage_category_id.capacity_ids,
            self.cardboxes_location_storage_type,
        )
        special_cardbox = self.env["stock.storage.category"].create(
            {
                "name": "Special Cardboxes",
            }
        )
        # If I change on a child, it will only be applied on this child
        special_cardboxes = self.cardboxes_location_storage_type.copy(
            {"storage_category_id": special_cardbox.id}
        )
        self.cardboxes_bin_1.storage_category_id = special_cardbox
        self.assertEqual(
            self.cardboxes_bin_1.computed_storage_category_id.capacity_ids,
            special_cardboxes,
        )
        # and not on his parent nor siblings
        self.assertEqual(
            self.cardboxes_stock.computed_storage_category_id.capacity_ids,
            self.cardboxes_location_storage_type,
        )
        self.assertEqual(
            self.cardboxes_bin_2.computed_storage_category_id.capacity_ids,
            self.cardboxes_location_storage_type,
        )
        self.assertEqual(
            self.cardboxes_bin_3.computed_storage_category_id.capacity_ids,
            self.cardboxes_location_storage_type,
        )
        # If I create a child bin on cardboxes bin 1, it will use the first
        #  parent's storage type
        bin_1_child = self.env["stock.location"].create(
            {"name": "Carboxes bin 1 child", "location_id": self.cardboxes_bin_1.id}
        )
        self.assertEqual(
            bin_1_child.computed_storage_category_id.capacity_ids, special_cardboxes
        )

    def test_location_leaf_locations(self):
        cardboxes_leaves = self.env["stock.location"].search(
            [("id", "child_of", self.cardboxes_stock.id), ("child_ids", "=", False)]
        )

        self.assertEqual(self.cardboxes_stock.leaf_location_ids, cardboxes_leaves)
        all_stock_leaves = self.env["stock.location"].search(
            [("id", "child_of", self.stock_location.id), ("child_ids", "=", False)]
        )
        self.assertEqual(self.stock_location.leaf_location_ids, all_stock_leaves)

    def test_location_leaf_locations_on_leaf(self):
        self.cardboxes_bin_4.active = False
        self.assertEqual(
            self.cardboxes_stock.leaf_location_ids,
            self.cardboxes_bin_1 | self.cardboxes_bin_2 | self.cardboxes_bin_3,
        )

    def test_location_max_height(self):
        self.pallets_location_storage_type.storage_category_id.max_height = 2
        self.cardboxes_location_storage_type.storage_category_id.max_height = 0
        category_id = self.pallets_location_storage_type.storage_category_id.id
        test_location = self.env["stock.location"].create(
            {
                "name": "TEST",
                "storage_category_id": category_id,
            }
        )
        # Should be the max height of pallets storage category (2)
        self.assertEqual(test_location.max_height, 2)
        self.cardboxes_location_storage_type.storage_category_id.max_height = 1
        test_location.storage_category_id = (
            self.cardboxes_location_storage_type.storage_category_id
        )
        # Should be the max height of cardboxes storage category (2)
        self.assertEqual(test_location.max_height, 1)

    def test_storage_type_max_height_in_meters(self):
        # Set the 'max_height' as meters and check that 'max_height_in_m' is equal
        uom_meter = self.env.ref("uom.product_uom_meter")
        self.pallets_location_storage_type.storage_category_id.length_uom_id = uom_meter
        self.pallets_location_storage_type.storage_category_id.max_height = 100
        self.assertEqual(
            self.pallets_location_storage_type.storage_category_id.max_height_in_m, 100
        )
        # Then set the UoM to centimeters and check that max_height_in_m is
        # reduced by a factor 100
        uom_cm = self.env.ref("uom.product_uom_cm")
        self.pallets_location_storage_type.storage_category_id.length_uom_id = uom_cm
        self.assertEqual(
            self.pallets_location_storage_type.storage_category_id.max_height_in_m, 1
        )

    def test_archive_package_storage_type(self):
        target = self.env.ref("stock_storage_type.package_storage_type_pallets")
        all_package_storage_types = self.env["stock.package.type"].search([])
        self.assertIn(target, all_package_storage_types)
        target.active = False
        all_package_storage_types = self.env["stock.package.type"].search([])
        self.assertNotIn(target, all_package_storage_types)

    def test_package_message(self):
        """
        Test for the message displayed on Stock Package Type forms
        """
        pallets = self.env.ref("stock_storage_type.package_storage_type_pallets")
        message = "When a package with storage type Pallets is put away, the "
        message += "strategy will look for an allowed location in the "
        message += "following locations:"
        self.assertIn(message, pallets.storage_type_message)

        message = (
            "Pallets reserve storage area (WARNING: restrictions are active on "
            "location storage types matching this package storage type)"
        )

        self.assertIn(message, pallets.storage_type_message)

    def test_sequence_to_location_menu(self):
        action = self.location_sequence_pallet.button_show_locations()
        self.assertIn(
            (
                "computed_storage_capacity_ids",
                "in",
                self.location_sequence_pallet.package_type_id.storage_category_capacity_ids.ids,
            ),
            action["domain"],
        )

    def test_storage_capacity_display(self):
        self.assertEqual(
            self.cardboxes_stock.computed_storage_category_id.capacity_ids.display_name,
            "Cardboxes x 1.0 (Package: Cardboxes - Allow New Product: Allow mixed products)",
        )
