# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from .common import TestStorageTypeCommon


class TestStockLocation(TestStorageTypeCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        ref = cls.env.ref
        cls.areas.write({"pack_putaway_strategy": "ordered_locations"})
        cls.pallets_reserve_bin_1_location = ref(
            "stock_storage_type.stock_location_pallets_reserve_bin_1"
        )
        cls.pallets_reserve_bin_2_location = ref(
            "stock_storage_type.stock_location_pallets_reserve_bin_2"
        )
        cls.pallets_reserve_bin_3_location = ref(
            "stock_storage_type.stock_location_pallets_reserve_bin_3"
        )

    def test_get_ordered_leaf_locations(self):
        # Test with the same max_height on all related storage types (0 here)
        self.assertEqual(
            self.areas._get_ordered_leaf_locations().ids,
            (
                self.cardboxes_bin_1_location
                | self.cardboxes_bin_2_location
                | self.cardboxes_bin_3_location
                | self.cardboxes_bin_4_location
                | self.pallets_bin_1_location
                | self.pallets_bin_2_location
                | self.pallets_bin_3_location
                | self.pallets_reserve_bin_1_location
                | self.pallets_reserve_bin_2_location
                | self.pallets_reserve_bin_3_location
            ).ids,
        )
        # Set the max_height on pallets storage type higher than the others
        self.pallets_location_storage_type.max_height = 2
        self.cardboxes_location_storage_type.max_height = 1
        self.assertEqual(
            self.areas._get_ordered_leaf_locations().ids,
            (
                self.cardboxes_bin_1_location
                | self.cardboxes_bin_2_location
                | self.cardboxes_bin_3_location
                | self.cardboxes_bin_4_location
                | self.pallets_bin_1_location
                | self.pallets_bin_2_location
                | self.pallets_bin_3_location
                | self.pallets_reserve_bin_1_location
                | self.pallets_reserve_bin_2_location
                | self.pallets_reserve_bin_3_location
            ).ids,
        )
        # Set the max_height on cardboxes storage type higher than the others
        self.pallets_location_storage_type.max_height = 1
        self.cardboxes_location_storage_type.max_height = 2
        self.assertEqual(
            self.areas._get_ordered_leaf_locations().ids,
            (
                self.pallets_bin_1_location
                | self.pallets_bin_2_location
                | self.pallets_bin_3_location
                | self.pallets_reserve_bin_1_location
                | self.pallets_reserve_bin_2_location
                | self.pallets_reserve_bin_3_location
                | self.cardboxes_bin_1_location
                | self.cardboxes_bin_2_location
                | self.cardboxes_bin_3_location
                | self.cardboxes_bin_4_location
            ).ids,
        )
