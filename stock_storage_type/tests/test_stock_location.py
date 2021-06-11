# -*- coding: utf-8 -*-
# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from .common import TestStorageTypeCommon


class TestStockLocation(TestStorageTypeCommon):
    @classmethod
    def setUpClass(cls):
        super(TestStockLocation, cls).setUpClass()
        ref = cls.env.ref
        cls.pallets_reserve_bin_1_location = ref(
            "stock_storage_type.stock_location_pallets_reserve_bin_1"
        )
        cls.pallets_reserve_bin_2_location = ref(
            "stock_storage_type.stock_location_pallets_reserve_bin_2"
        )
        cls.pallets_reserve_bin_3_location = ref(
            "stock_storage_type.stock_location_pallets_reserve_bin_3"
        )
        cls.pallets_reserve_bin_4_location = ref(
            "stock_storage_type.stock_location_pallets_reserve_bin_4"
        )

    def test_get_ordered_leaf_locations(self):
        sublocation = self.stock_location.copy(
            {
                "name": "Sub-location",
                "pack_putaway_strategy": "ordered_locations",
                "location_id": self.stock_location.id,
            }
        )
        self.areas.write({"location_id": sublocation.id})

        # Test with the same max_height on all related storage types (0 here)
        ordered_locations = sublocation.get_storage_locations(self.product)
        self.assertEqual(
            ordered_locations.ids,
            (
                self.cardboxes_bin_1_location
                | self.cardboxes_bin_2_location
                | self.cardboxes_bin_3_location
                | self.cardboxes_bin_4_location
                | self.pallets_bin_1_location
                | self.pallets_bin_2_location
                | self.pallets_bin_3_location
                | self.pallets_bin_4_location
                | self.pallets_reserve_bin_1_location
                | self.pallets_reserve_bin_2_location
                | self.pallets_reserve_bin_3_location
                | self.pallets_reserve_bin_4_location
            ).ids,
        )
        # Set the max_height on pallets storage type higher than the others
        self.pallets_location_storage_type.max_height = 2
        self.cardboxes_location_storage_type.max_height = 1
        ordered_locations = sublocation.get_storage_locations(self.product)
        self.assertEqual(
            ordered_locations.ids,
            (
                self.cardboxes_bin_1_location
                | self.cardboxes_bin_2_location
                | self.cardboxes_bin_3_location
                | self.cardboxes_bin_4_location
                | self.pallets_bin_1_location
                | self.pallets_bin_2_location
                | self.pallets_bin_3_location
                | self.pallets_bin_4_location
                | self.pallets_reserve_bin_1_location
                | self.pallets_reserve_bin_2_location
                | self.pallets_reserve_bin_3_location
                | self.pallets_reserve_bin_4_location
            ).ids,
        )
        # Set the max_height on cardboxes storage type higher than the others
        self.pallets_location_storage_type.max_height = 1
        self.cardboxes_location_storage_type.max_height = 2
        ordered_locations = sublocation.get_storage_locations(self.product)
        self.assertEqual(
            ordered_locations.ids,
            (
                self.pallets_bin_1_location
                | self.pallets_bin_2_location
                | self.pallets_bin_3_location
                | self.pallets_bin_4_location
                | self.pallets_reserve_bin_1_location
                | self.pallets_reserve_bin_2_location
                | self.pallets_reserve_bin_3_location
                | self.pallets_reserve_bin_4_location
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

        location.allowed_location_storage_type_ids.do_not_mix_products = False
        self.assertEqual(
            location.location_will_contain_product_ids,
            self.env["product.product"].browse(),
        )

    def test_will_contain_product_ids_2(self):
        """
        Test that canceled move and are not taken into account

        Before the use of stock_operation_cleaner, when a move was cancelled
        the pack operation was not deleted. Therefore the incoming qty on the
        stock location was not right since it also take into account the
        pack operations linked to the location
        """
        location = self.pallets_bin_1_location
        location.allowed_location_storage_type_ids.only_empty = False
        location.allowed_location_storage_type_ids.do_not_mix_products = True

        self._update_qty_in_location(location, self.product, 10)
        self.assertEqual(location.location_will_contain_product_ids, self.product)

        loc_supplier_id = self.env.ref("stock.stock_location_suppliers").id
        StockMove = self.env["stock.move"]
        StockPicking = self.env["stock.picking"]
        self.picking = StockPicking.create(
            {
                "picking_type_id": self.env.ref("stock.picking_type_in").id,
                "location_id": loc_supplier_id,
                "location_dest_id": location.id,
            }
        )
        sm = StockMove.create(
            {
                "name": "/",
                "picking_id": self.picking.id,
                "product_uom": self.product2.uom_id.id,
                "location_id": loc_supplier_id,
                "location_dest_id": location.id,
                "product_id": self.product2.id,
                "product_uom_qty": 10,
            }
        )
        self.picking.action_confirm()
        self.assertEqual(
            location.location_will_contain_product_ids, self.product | self.product2
        )

        sm.action_cancel()
        self.assertEqual(location.location_will_contain_product_ids, self.product)

    def test_will_contain_lot_ids(self):
        location = self.pallets_bin_1_location
        location.allowed_location_storage_type_ids.only_empty = False
        location.allowed_location_storage_type_ids.do_not_mix_products = True
        location.allowed_location_storage_type_ids.do_not_mix_lots = True
        lot_values = {"product_id": self.product.id}
        lot1 = self.env["stock.production.lot"].create(lot_values)

        self._update_qty_in_location(location, self.product, 10, lot=lot1)
        self.assertEqual(location.location_will_contain_lot_ids, lot1)

        location.allowed_location_storage_type_ids.do_not_mix_lots = False
        self.assertEqual(
            location.location_will_contain_lot_ids,
            self.env["stock.production.lot"].browse(),
        )

    def test_location_is_empty_non_internal(self):
        location = self.env.ref("stock.stock_location_customers")
        # we always consider an non-internal location empty, the put-away
        # rules do not apply and we can add as many quants as we want
        self.assertTrue(location.location_is_empty)
        self._update_qty_in_location(location, self.product, 10)
        self.assertTrue(location.location_is_empty)

    def test_location_is_empty(self):
        location = self.pallets_reserve_bin_1_location
        self.assertTrue(location.allowed_location_storage_type_ids.only_empty)
        self.assertTrue(location.location_is_empty)
        self._update_qty_in_location(location, self.product, 10)
        self.assertFalse(location.location_is_empty)

        # When the location has no "only_empty" storage type, we don't
        # care about if it is empty or not, we keep it as True so we
        # can always put things inside. Not computing it prevents
        # useless race conditions on concurrent writes.
        location.allowed_location_storage_type_ids.only_empty = False
        self.assertTrue(location.location_is_empty)
