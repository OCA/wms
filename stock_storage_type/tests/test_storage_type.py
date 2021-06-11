# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo.exceptions import ValidationError
from odoo.tests import SavepointCase


class TestStorageType(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

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
            self.cardboxes_stock.location_storage_type_ids,
            self.cardboxes_location_storage_type,
        )
        # It is what's allowed on the parent stock
        self.assertEqual(
            self.cardboxes_stock.allowed_location_storage_type_ids,
            self.cardboxes_location_storage_type,
        )
        # and also what's allowed on the children
        self.assertEqual(
            self.cardboxes_bin_1.allowed_location_storage_type_ids,
            self.cardboxes_location_storage_type,
        )
        self.assertEqual(
            self.cardboxes_bin_2.allowed_location_storage_type_ids,
            self.cardboxes_location_storage_type,
        )
        self.assertEqual(
            self.cardboxes_bin_3.allowed_location_storage_type_ids,
            self.cardboxes_location_storage_type,
        )
        # If I change on a child, it will only be applied on this child
        special_cardboxes = self.cardboxes_location_storage_type.copy(
            {"name": "special cardboxes"}
        )
        self.cardboxes_bin_1.write(
            {"location_storage_type_ids": [(6, 0, special_cardboxes.ids)]}
        )
        self.assertEqual(
            self.cardboxes_bin_1.allowed_location_storage_type_ids, special_cardboxes
        )
        # and not on his parent nor siblings
        self.assertEqual(
            self.cardboxes_stock.allowed_location_storage_type_ids,
            self.cardboxes_location_storage_type,
        )
        self.assertEqual(
            self.cardboxes_bin_2.allowed_location_storage_type_ids,
            self.cardboxes_location_storage_type,
        )
        self.assertEqual(
            self.cardboxes_bin_3.allowed_location_storage_type_ids,
            self.cardboxes_location_storage_type,
        )
        # If I create a child bin on cardboxes bin 1, it will use the first
        #  parent's storage type
        bin_1_child = self.env["stock.location"].create(
            {"name": "Carboxes bin 1 child", "location_id": self.cardboxes_bin_1.id}
        )
        self.assertEqual(
            bin_1_child.allowed_location_storage_type_ids, special_cardboxes
        )

    def test_location_storage_type_constraints_definition(self):
        # Cannot set do not mix lots without do not mix products
        with self.assertRaises(ValidationError):
            self.pallets_location_storage_type.do_not_mix_lots = True
        self.pallets_location_storage_type.do_not_mix_lots = False
        self.pallets_location_storage_type.only_empty = False
        self.pallets_location_storage_type.do_not_mix_products = True
        self.pallets_location_storage_type.do_not_mix_lots = True

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
        self.assertEqual(self.cardboxes_bin_3.leaf_location_ids, self.cardboxes_bin_3)

    def test_location_max_height(self):
        self.pallets_location_storage_type.max_height = 2
        self.pallets_uk_location_storage_type.max_height = 3
        self.cardboxes_location_storage_type.max_height = 0
        test_location = self.env["stock.location"].create(
            {
                "name": "TEST",
                "location_storage_type_ids": [
                    (
                        6,
                        0,
                        [
                            self.pallets_location_storage_type.id,
                            self.pallets_uk_location_storage_type.id,
                            self.cardboxes_location_storage_type.id,
                        ],
                    ),
                ],
            }
        )
        self.assertEqual(test_location.max_height, 0)
        self.cardboxes_location_storage_type.max_height = 1
        self.assertEqual(test_location.max_height, 3)

    def test_archive_package_storage_type(self):
        target = self.env.ref("stock_storage_type.package_storage_type_pallets")
        all_package_storage_types = self.env["stock.package.storage.type"].search([])
        self.assertIn(target, all_package_storage_types)
        target.active = False
        all_package_storage_types = self.env["stock.package.storage.type"].search([])
        self.assertNotIn(target, all_package_storage_types)

    def test_archive_location_storage_type(self):
        target = self.env.ref("stock_storage_type.location_storage_type_pallets")
        all_location_storage_types = self.env["stock.location.storage.type"].search([])
        self.assertIn(target, all_location_storage_types)
        target.active = False
        all_location_storage_types = self.env["stock.location.storage.type"].search([])
        self.assertNotIn(target, all_location_storage_types)
