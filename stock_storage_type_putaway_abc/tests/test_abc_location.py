# Copyright 2019-2021 Camptocamp SA
# Copyright 2019-2021 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo.tests import SavepointCase


class TestAbcLocation(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        ref = cls.env.ref
        cls.cardboxes_location_storage_type = ref(
            "stock_storage_type.location_storage_type_cardboxes"
        )
        cls.pallets_location_storage_type = ref(
            "stock_storage_type.location_storage_type_pallets"
        )
        cls.stock_location = ref("stock.stock_location_stock")
        cls.cardboxes_location = ref("stock_storage_type.stock_location_cardboxes")
        cls.pallets_location = ref("stock_storage_type.stock_location_pallets")
        cls.cardboxes_bin_a_location = ref(
            "stock_storage_type.stock_location_cardboxes_bin_2"
        )
        cls.cardboxes_bin_b1_location = ref(
            "stock_storage_type.stock_location_cardboxes_bin_4"
        )
        cls.cardboxes_bin_b2_location = ref(
            "stock_storage_type.stock_location_cardboxes_bin_1"
        )
        cls.cardboxes_bin_c_location = ref(
            "stock_storage_type.stock_location_cardboxes_bin_3"
        )
        cls.pallets_bin_a_location = ref(
            "stock_storage_type.stock_location_pallets_bin_3"
        )
        cls.pallets_bin_b1_location = ref(
            "stock_storage_type.stock_location_pallets_bin_4"
        )
        cls.pallets_bin_b2_location = ref(
            "stock_storage_type.stock_location_pallets_bin_2"
        )
        cls.pallets_bin_c_location = ref(
            "stock_storage_type.stock_location_pallets_bin_1"
        )
        cls.product = ref("product.product_product_9")

    def test_display_abc_storage_one_level(self):
        self.cardboxes_location.write({"pack_putaway_strategy": "abc"})
        self.assertTrue(self.cardboxes_bin_a_location.display_abc_storage)
        self.assertTrue(self.cardboxes_bin_b1_location.display_abc_storage)
        self.assertTrue(self.cardboxes_bin_b2_location.display_abc_storage)
        self.assertTrue(self.cardboxes_bin_c_location.display_abc_storage)
        self.assertFalse(self.pallets_bin_a_location.display_abc_storage)
        self.assertFalse(self.pallets_bin_b1_location.display_abc_storage)
        self.assertFalse(self.pallets_bin_b2_location.display_abc_storage)
        self.assertFalse(self.pallets_bin_c_location.display_abc_storage)
        self.cardboxes_location.write({"pack_putaway_strategy": "ordered_locations"})
        self.assertFalse(self.cardboxes_bin_a_location.display_abc_storage)
        self.assertFalse(self.cardboxes_bin_b1_location.display_abc_storage)
        self.assertFalse(self.cardboxes_bin_b2_location.display_abc_storage)
        self.assertFalse(self.cardboxes_bin_c_location.display_abc_storage)
        self.assertFalse(self.pallets_bin_a_location.display_abc_storage)
        self.assertFalse(self.pallets_bin_b1_location.display_abc_storage)
        self.assertFalse(self.pallets_bin_b2_location.display_abc_storage)
        self.assertFalse(self.pallets_bin_c_location.display_abc_storage)

    def test_display_abc_storage_two_levels(self):
        self.stock_location.write({"pack_putaway_strategy": "abc"})
        self.assertTrue(self.cardboxes_bin_a_location.display_abc_storage)
        self.assertTrue(self.cardboxes_bin_b1_location.display_abc_storage)
        self.assertTrue(self.cardboxes_bin_b2_location.display_abc_storage)
        self.assertTrue(self.cardboxes_bin_c_location.display_abc_storage)
        self.assertTrue(self.pallets_bin_a_location.display_abc_storage)
        self.assertTrue(self.pallets_bin_b1_location.display_abc_storage)
        self.assertTrue(self.pallets_bin_b2_location.display_abc_storage)
        self.assertTrue(self.pallets_bin_c_location.display_abc_storage)
        self.stock_location.write({"pack_putaway_strategy": "none"})
        self.assertFalse(self.cardboxes_bin_a_location.display_abc_storage)
        self.assertFalse(self.cardboxes_bin_b1_location.display_abc_storage)
        self.assertFalse(self.cardboxes_bin_b2_location.display_abc_storage)
        self.assertFalse(self.cardboxes_bin_c_location.display_abc_storage)
        self.assertFalse(self.pallets_bin_a_location.display_abc_storage)
        self.assertFalse(self.pallets_bin_b1_location.display_abc_storage)
        self.assertFalse(self.pallets_bin_b2_location.display_abc_storage)
        self.assertFalse(self.pallets_bin_c_location.display_abc_storage)

    def test_abc_ordered(self):
        self.cardboxes_location.write({"pack_putaway_strategy": "abc"})
        self.cardboxes_bin_a_location.write(
            {"abc_storage": "a", "pack_putaway_sequence": 3}
        )
        self.cardboxes_bin_b1_location.write(
            {"abc_storage": "b", "pack_putaway_sequence": 1}
        )
        self.cardboxes_bin_b2_location.write(
            {"abc_storage": "b", "pack_putaway_sequence": 2}
        )
        self.cardboxes_bin_c_location.write(
            {"abc_storage": "c", "pack_putaway_sequence": 1}
        )
        self.product.write({"abc_storage": "a"})
        ordered_locations = self.cardboxes_location.get_storage_locations(self.product)
        self.assertEqual(
            ordered_locations.ids,
            (
                self.cardboxes_bin_a_location
                | self.cardboxes_bin_b1_location
                | self.cardboxes_bin_b2_location
                | self.cardboxes_bin_c_location
            ).ids,
        )
        self.product.write({"abc_storage": "b"})
        ordered_locations = self.cardboxes_location.get_storage_locations(self.product)
        self.assertEqual(
            ordered_locations.ids,
            (
                self.cardboxes_bin_b1_location
                | self.cardboxes_bin_b2_location
                | self.cardboxes_bin_c_location
                | self.cardboxes_bin_a_location
            ).ids,
        )
        self.product.write({"abc_storage": "c"})
        ordered_locations = self.cardboxes_location.get_storage_locations(self.product)
        self.assertEqual(
            ordered_locations.ids,
            (
                self.cardboxes_bin_c_location
                | self.cardboxes_bin_b1_location
                | self.cardboxes_bin_b2_location
                | self.cardboxes_bin_a_location
            ).ids,
        )

    def test_abc_ordered_with_height(self):
        # configure stock locations to put an intermediate level between
        # Stock/ and leaf locations (to ease the tests)
        sublocation = self.stock_location.copy(
            {"name": "Sub-location", "location_id": self.stock_location.id}
        )
        (self.cardboxes_location | self.pallets_location).location_id = sublocation
        # configure putaway strategy for all locations
        sublocation.write({"pack_putaway_strategy": "abc"})
        # configure abc storage on locations
        self.cardboxes_bin_a_location.write({"abc_storage": "a"})
        self.cardboxes_bin_b1_location.write(
            {"abc_storage": "b", "pack_putaway_sequence": 1}
        )
        self.cardboxes_bin_b2_location.write(
            {"abc_storage": "b", "pack_putaway_sequence": 2}
        )
        self.cardboxes_bin_c_location.write({"abc_storage": "c"})
        self.pallets_bin_a_location.write({"abc_storage": "a"})
        self.pallets_bin_b1_location.write(
            {"abc_storage": "b", "pack_putaway_sequence": 1}
        )
        self.pallets_bin_b2_location.write(
            {"abc_storage": "b", "pack_putaway_sequence": 2}
        )
        self.pallets_bin_c_location.write({"abc_storage": "c"})
        # Test with a product abc_storage=A
        #   - with max height on pallets storage type higher than the cardboxes one
        self.product.write({"abc_storage": "a"})
        self.pallets_location_storage_type.max_height = 3
        self.cardboxes_location_storage_type.max_height = 1
        ordered_locations = sublocation.get_storage_locations(self.product)
        self.assertEqual(
            ordered_locations.ids,
            (
                self.cardboxes_bin_a_location
                | self.cardboxes_bin_b1_location
                | self.cardboxes_bin_b2_location
                | self.cardboxes_bin_c_location
                | self.pallets_bin_a_location
                | self.pallets_bin_b1_location
                | self.pallets_bin_b2_location
                | self.pallets_bin_c_location
            ).ids,
        )
        #   - with max height on cardboxes storage type higher than the pallets one
        self.pallets_location_storage_type.max_height = 1
        self.cardboxes_location_storage_type.max_height = 2
        ordered_locations = sublocation.get_storage_locations(self.product)
        self.assertEqual(
            ordered_locations.ids,
            (
                self.pallets_bin_a_location
                | self.pallets_bin_b1_location
                | self.pallets_bin_b2_location
                | self.pallets_bin_c_location
                | self.cardboxes_bin_a_location
                | self.cardboxes_bin_b1_location
                | self.cardboxes_bin_b2_location
                | self.cardboxes_bin_c_location
            ).ids,
        )
        #   - with max height "no-limit" on pallets storage type
        self.pallets_location_storage_type.max_height = 0
        self.cardboxes_location_storage_type.max_height = 2
        ordered_locations = sublocation.get_storage_locations(self.product)
        self.assertEqual(
            ordered_locations.ids,
            (
                self.cardboxes_bin_a_location
                | self.cardboxes_bin_b1_location
                | self.cardboxes_bin_b2_location
                | self.cardboxes_bin_c_location
                | self.pallets_bin_a_location
                | self.pallets_bin_b1_location
                | self.pallets_bin_b2_location
                | self.pallets_bin_c_location
            ).ids,
        )
        # Test with a product abc_storage=B
        #   - with max height on pallets storage type higher than the cardboxes one
        self.product.write({"abc_storage": "b"})
        self.pallets_location_storage_type.max_height = 3
        self.cardboxes_location_storage_type.max_height = 1
        ordered_locations = sublocation.get_storage_locations(self.product)
        self.assertEqual(
            ordered_locations.ids,
            (
                self.cardboxes_bin_b1_location
                | self.cardboxes_bin_b2_location
                | self.cardboxes_bin_c_location
                | self.cardboxes_bin_a_location
                | self.pallets_bin_b1_location
                | self.pallets_bin_b2_location
                | self.pallets_bin_c_location
                | self.pallets_bin_a_location
            ).ids,
        )
        #   - with max height on cardboxes storage type higher than the pallets one
        self.pallets_location_storage_type.max_height = 1
        self.cardboxes_location_storage_type.max_height = 2
        ordered_locations = sublocation.get_storage_locations(self.product)
        self.assertEqual(
            ordered_locations.ids,
            (
                self.pallets_bin_b1_location
                | self.pallets_bin_b2_location
                | self.pallets_bin_c_location
                | self.pallets_bin_a_location
                | self.cardboxes_bin_b1_location
                | self.cardboxes_bin_b2_location
                | self.cardboxes_bin_c_location
                | self.cardboxes_bin_a_location
            ).ids,
        )
        #   - with max height "no-limit" on pallets storage type
        self.pallets_location_storage_type.max_height = 0
        self.cardboxes_location_storage_type.max_height = 2
        ordered_locations = sublocation.get_storage_locations(self.product)
        self.assertEqual(
            ordered_locations.ids,
            (
                self.cardboxes_bin_b1_location
                | self.cardboxes_bin_b2_location
                | self.cardboxes_bin_c_location
                | self.cardboxes_bin_a_location
                | self.pallets_bin_b1_location
                | self.pallets_bin_b2_location
                | self.pallets_bin_c_location
                | self.pallets_bin_a_location
            ).ids,
        )

    def test_get_storage_locations_not_all_keys(self):
        """Do not crash if we have no A or B or C locations"""
        self.stock_location.write({"pack_putaway_strategy": "abc"})
        self.env["stock.location"].search(
            [("abc_storage", "in", ("a", "b"))]
        ).abc_storage = "b"
        self.assertTrue(self.stock_location.get_storage_locations(self.product))
