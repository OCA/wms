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

    def test_will_contain_product_ids(self):
        location = self.pallets_bin_1_location
        location.allowed_location_storage_type_ids.only_empty = False
        location.allowed_location_storage_type_ids.do_not_mix_products = True

        self._update_qty_in_location(location, self.product, 10)
        self.assertEqual(location.location_will_contain_product_ids, self.product)

        # the moves and move lines created are not really valid, but we don't care, it's
        # only to have "in_move_ids" and "in_move_line_ids" on the location
        self.env["stock.move"].create(
            {
                "name": "test",
                "product_id": self.product2.id,
                "location_id": self.stock_location.id,
                "location_dest_id": location.id,
                "product_uom": self.product2.uom_id.id,
                "product_uom_qty": 10,
                "state": "waiting",
            }
        )
        self.assertEqual(
            location.location_will_contain_product_ids, self.product | self.product2
        )

        ml_move = self.env["stock.move"].create(
            {
                "name": "test",
                "product_id": self.product3.id,
                "location_id": self.stock_location.id,
                "location_dest_id": location.location_id.id,
                "product_uom": self.product2.uom_id.id,
                "product_uom_qty": 10,
                "state": "waiting",
            }
        )
        self.env["stock.move.line"].create(
            {
                "product_id": self.product3.id,
                "location_id": self.stock_location.id,
                "location_dest_id": location.id,
                "product_uom_id": self.product3.uom_id.id,
                "product_uom_qty": 10,
                "move_id": ml_move.id,
                "company_id": self.env.company.id,
            }
        )
        self.assertEqual(
            location.location_will_contain_product_ids,
            self.product | self.product2 | self.product3,
        )

        location.allowed_location_storage_type_ids.do_not_mix_products = False
        self.assertEqual(
            location.location_will_contain_product_ids,
            self.env["product.product"].browse(),
        )

    def test_will_contain_lot_ids(self):
        location = self.pallets_bin_1_location
        location.allowed_location_storage_type_ids.only_empty = False
        location.allowed_location_storage_type_ids.do_not_mix_products = True
        location.allowed_location_storage_type_ids.do_not_mix_lots = True
        lot_values = {"product_id": self.product.id, "company_id": self.env.company.id}
        lot1 = self.env["stock.production.lot"].create(lot_values)
        lot2 = self.env["stock.production.lot"].create(lot_values)

        self._update_qty_in_location(location, self.product, 10, lot=lot1)
        self.assertEqual(location.location_will_contain_lot_ids, lot1)

        # the moves and move lines created are not really valid, but we don't care, it's
        # only to have "in_move_ids" and "in_move_line_ids" on the location
        ml_move = self.env["stock.move"].create(
            {
                "name": "test",
                "product_id": self.product.id,
                "location_id": self.stock_location.id,
                "location_dest_id": location.location_id.id,
                "product_uom": self.product2.uom_id.id,
                "product_uom_qty": 10,
                "state": "waiting",
            }
        )
        self.env["stock.move.line"].create(
            {
                "product_id": self.product.id,
                "lot_id": lot2.id,
                "location_id": self.stock_location.id,
                "location_dest_id": location.id,
                "product_uom_id": self.product.uom_id.id,
                "product_uom_qty": 10,
                "move_id": ml_move.id,
                "company_id": self.env.company.id,
            }
        )
        self.assertEqual(location.location_will_contain_lot_ids, lot1 | lot2)

        location.allowed_location_storage_type_ids.do_not_mix_lots = False
        self.assertEqual(
            location.location_will_contain_lot_ids,
            self.env["stock.production.lot"].browse(),
        )
