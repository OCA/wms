# -*- coding: utf-8 -*-
# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from .common import TestStorageTypeCommon


class TestStockLocation2(TestStorageTypeCommon):
    @classmethod
    def setUpClass(cls):
        super(TestStockLocation2, cls).setUpClass()
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
        loc_supplier_id = cls.env.ref("stock.stock_location_suppliers").id

        # create a picking to pallets_bin_1_location
        location = cls.pallets_bin_1_location
        StockMove = cls.env["stock.move"]
        StockPicking = cls.env["stock.picking"]
        cls.picking = StockPicking.create(
            {
                "picking_type_id": cls.env.ref("stock.picking_type_in").id,
                "location_id": loc_supplier_id,
                "location_dest_id": location.id,
            }
        )
        cls.stock_move_p2 = StockMove.create(
            {
                "name": "/",
                "picking_id": cls.picking.id,
                "product_uom": cls.product2.uom_id.id,
                "location_id": loc_supplier_id,
                "location_dest_id": location.id,
                "product_id": cls.product2.id,
                "product_uom_qty": 10,
            }
        )
        cls.stock_move_p3 = StockMove.create(
            {
                "name": "/",
                "picking_id": cls.picking.id,
                "product_uom": cls.product3.uom_id.id,
                "location_id": loc_supplier_id,
                "location_dest_id": location.id,
                "product_id": cls.product3.id,
                "product_uom_qty": 10,
            }
        )

    def test_will_contain_product_ids(self):
        """
        Test that cancelled move are not taken into account

        Before the use of stock_operation_cleaner, when a move was cancelled
        the pack operation was not deleted. Therefore the incoming qty on the
        stock location was not right since it also take into account the
        pack operations linked to the location
        """
        location = self.pallets_bin_1_location
        location.allowed_location_storage_type_ids.only_empty = False
        location.allowed_location_storage_type_ids.do_not_mix_products = True

        self._update_qty_in_location(location, self.product, 10)
        # at this stage, the picking is still in draft.
        self.assertEqual(location.location_will_contain_product_ids, self.product)

        self.picking.action_confirm()
        self.assertEqual(
            location.location_will_contain_product_ids,
            self.product | self.product2 | self.product3,
        )

        self.stock_move_p2.action_cancel()
        self.assertEqual(
            location.location_will_contain_product_ids, self.product | self.product3
        )

    def test_will_contain_product_ids_2(self):
        """
        Data:
            A draft picking with product 2 and product 2 with
            pallets_bin_1_location as destination
        Test case:
            1. Confirm the picking
            2. Unreserve the picking
            3. Set moves to draft
        Expected results:
            1. product 2 and product 3 are expected into pallets_bin_1_location
            2. product 2 and product 3 are still expected into pallets_bin_1_location
            since even if pack operations are deleted, the stock moves are confirmed
            2. product 2 and product 3 are not more expected into
            pallets_bin_1_location since move are in state draft
        """
        location = self.pallets_bin_1_location
        location.allowed_location_storage_type_ids.only_empty = False
        location.allowed_location_storage_type_ids.do_not_mix_products = True

        self.assertFalse(location.location_will_contain_product_ids)

        # 1
        self.picking.action_confirm()
        self.assertEqual(
            location.location_will_contain_product_ids, self.product2 | self.product3
        )
        # 2
        self.picking.do_unreserve()
        self.assertEqual(
            location.location_will_contain_product_ids, self.product2 | self.product3
        )

        # 3
        self.picking.move_lines.write({"state": "draft"})
        self.assertFalse(location.location_will_contain_product_ids)
