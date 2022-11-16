# Copyright 2022 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from .common import ABCClassificationLevelCase


class TestProduct(ABCClassificationLevelCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ABCClassificationProfile._fields["profile_type"].selection = [
            ("sale_stock", "Sale Stock")
        ]
        cls.classification_profile_sale_stock = cls.env.ref(
            "product_abc_classification_sale_stock.abc_classification_profile_sale_stock"
        )
        levels = cls.classification_profile_sale_stock.level_ids
        cls.classification_level_a = levels.filtered(lambda l: l.name == "a")
        cls.classification_level_b = levels.filtered(lambda l: l.name == "b")
        cls.classification_level_c = levels.filtered(lambda l: l.name == "c")

        cls.cardboxes_location.write({"pack_putaway_strategy": "abc"})
        cls.cardboxes_bin_2_location.write(
            {"abc_storage": "a", "pack_putaway_sequence": 3}
        )
        cls.cardboxes_bin_4_location.write(
            {"abc_storage": "b", "pack_putaway_sequence": 1}
        )
        cls.cardboxes_bin_1_location.write(
            {"abc_storage": "b", "pack_putaway_sequence": 2}
        )
        cls.cardboxes_bin_3_location.write(
            {"abc_storage": "c", "pack_putaway_sequence": 1}
        )

        # Set classification profile on product
        cls.product.abc_classification_profile_ids = (
            cls.classification_profile_sale_stock
        )

        cls._set_warehouse_2()

    @classmethod
    def _set_warehouse_2(cls):
        # We configure multi warehouse - copying locations
        # We apply a different abc storage per location than first
        # warehouse
        cls.warehouse_2 = cls.env["stock.warehouse"].create(
            {"name": "Warehouse 2 (Company 1)", "code": "WH2"}
        )
        cls.wh_2_stock_location_cardboxes = cls.cardboxes_location.copy(
            {"location_id": cls.warehouse_2.lot_stock_id.id}
        )
        cls.wh_2_cardboxes_bin_1_location = cls.cardboxes_bin_1_location.copy(
            {"location_id": cls.wh_2_stock_location_cardboxes.id}
        )
        cls.wh_2_cardboxes_bin_2_location = cls.cardboxes_bin_2_location.copy(
            {"location_id": cls.wh_2_stock_location_cardboxes.id}
        )
        cls.wh_2_cardboxes_bin_3_location = cls.cardboxes_bin_3_location.copy(
            {"location_id": cls.wh_2_stock_location_cardboxes.id}
        )
        cls.wh_2_cardboxes_bin_4_location = cls.cardboxes_bin_4_location.copy(
            {"location_id": cls.wh_2_stock_location_cardboxes.id}
        )
        cls.wh_2_cardboxes_bin_1_location.write(
            {"abc_storage": "a", "pack_putaway_sequence": 2}
        )
        cls.wh_2_cardboxes_bin_2_location.write(
            {"abc_storage": "b", "pack_putaway_sequence": 3}
        )
        cls.wh_2_cardboxes_bin_3_location.write(
            {"abc_storage": "c", "pack_putaway_sequence": 1}
        )
        cls.wh_2_cardboxes_bin_4_location.write(
            {"abc_storage": "c", "pack_putaway_sequence": 2}
        )

        cls.wh2_profile = cls.env["abc.classification.profile"].create(
            {
                "name": "Sale Stock Profile WH2",
                "profile_type": "sale_stock",
                "warehouse_id": cls.warehouse_2.id,
                "period": "365",
                "level_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "a",
                            "percentage": 80,
                            "percentage_products": 20,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": "b",
                            "percentage": 15,
                            "percentage_products": 30,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": "c",
                            "percentage": 5,
                            "percentage_products": 50,
                        },
                    ),
                ],
            }
        )
        cls.product.abc_classification_profile_ids |= cls.wh2_profile

    def test_abc_storage_b(self):
        # Set putaway strategy on carboxes locations as 'abc',
        # Add an abc classification on product that should result in 'b' classification
        self.product_level_b = self.ProductLevel.create(
            {
                "product_id": self.product.id,
                "computed_level_id": self.classification_level_b.id,
                "profile_id": self.classification_profile_sale_stock.id,
            }
        )

        ordered_locations = self.cardboxes_location.get_storage_locations(self.product)
        # We check that location order is:
        # B (1), B (2), C, A
        self.assertEqual(
            ordered_locations.ids,
            (
                self.cardboxes_bin_4_location
                | self.cardboxes_bin_1_location
                | self.cardboxes_bin_3_location
                | self.cardboxes_bin_2_location
            ).ids,
        )

    def test_abc_storage_a(self):
        # Set putaway strategy on carboxes locations as 'abc',
        # Add an abc classification on product that should result in 'a' classification
        self.product_level_a = self.ProductLevel.create(
            {
                "product_id": self.product.id,
                "computed_level_id": self.classification_level_a.id,
                "profile_id": self.classification_profile_sale_stock.id,
            }
        )
        ordered_locations = self.cardboxes_location.get_storage_locations(self.product)
        # We check that location order is:
        # A, B (1), B (2), C
        self.assertEqual(
            ordered_locations.ids,
            (
                self.cardboxes_bin_2_location
                | self.cardboxes_bin_4_location
                | self.cardboxes_bin_1_location
                | self.cardboxes_bin_3_location
            ).ids,
        )

        self.wh2_product_level_a = self.ProductLevel.create(
            {
                "product_id": self.product.id,
                "computed_level_id": self.wh2_profile.level_ids.filtered(
                    lambda l: l.name == "a"
                ).id,
                "profile_id": self.wh2_profile.id,
            }
        )

        # We check the order for Warehouse 2
        ordered_locations = self.wh_2_stock_location_cardboxes.get_storage_locations(
            self.product
        )
        # We check that location order is:
        # A, B (1), B (2), C
        self.assertEqual(
            ordered_locations.ids,
            (
                self.wh_2_cardboxes_bin_1_location
                | self.wh_2_cardboxes_bin_2_location
                | self.wh_2_cardboxes_bin_3_location
                | self.wh_2_cardboxes_bin_4_location
            ).ids,
        )

        # We delete the profile for product on warehouse 2
        self.wh2_product_level_a.unlink()

        # We check the classification applied is fallback on abc_storage field
        # on product level

        self.assertEqual("b", self.product.abc_storage)
        ordered_locations = self.wh_2_stock_location_cardboxes.get_storage_locations(
            self.product
        )
        # We check that location order is:
        # B (1), B (2), C, A
        self.assertEqual(
            ordered_locations.ids,
            (
                self.wh_2_cardboxes_bin_2_location
                | self.wh_2_cardboxes_bin_3_location
                | self.wh_2_cardboxes_bin_4_location
                | self.wh_2_cardboxes_bin_1_location
            ).ids,
        )
