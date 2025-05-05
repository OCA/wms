# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from .common import TestStorageTypeCommon


class TestStockLocation(TestStorageTypeCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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
        # Set the max_height on pallets storage category higher than the others
        self.pallets_location_storage_type.storage_category_id.max_height = 2
        self.cardboxes_location_storage_type.storage_category_id.max_height = 1
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
        # Set the max_height on cardboxes storage category higher than the others
        self.pallets_location_storage_type.storage_category_id.max_height = 1
        self.cardboxes_location_storage_type.storage_category_id.max_height = 2
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
        location.computed_storage_category_id.allow_new_product = "same"

        self._update_qty_in_location(location, self.product, 10)
        self.assertEqual(location.location_will_contain_product_ids, self.product)

        # the moves and move lines created are not really valid, but we don't care,
        # its only to have "pending_in_move[_line]_ids" on the location
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
                "quantity": 10,
                "move_id": ml_move.id,
                "company_id": self.env.company.id,
            }
        )
        self.assertEqual(
            location.location_will_contain_product_ids,
            self.product | self.product2 | self.product3,
        )

        location.computed_storage_category_id.allow_new_product = "mixed"
        self.assertEqual(
            location.location_will_contain_product_ids,
            self.env["product.product"].browse(),
        )

    def test_will_contain_product_ids_quantity(self):
        """
        Put a product quantity in pallet bin 1 location
        Create a move that will void that location
        Transfer the quantity
        Odoo lets a quant with zero quantity
        The location_will_contain_product_ids should be void
        """
        location = self.pallets_bin_1_location
        location.computed_storage_category_id.allow_new_product = "same"

        self._update_qty_in_location(location, self.product, 10)
        self.assertEqual(location.location_will_contain_product_ids, self.product)
        ml_move = self.env["stock.move"].create(
            {
                "name": "test",
                "product_id": self.product.id,
                "location_id": location.id,
                "location_dest_id": self.env.ref("stock.stock_location_customers").id,
                "product_uom": self.product.uom_id.id,
                "product_uom_qty": 10,
            }
        )
        ml_move._action_confirm()
        ml_move._action_assign()

        ml_move.picked = True
        ml_move._action_done()
        # Odoo lets a zero quantity quant before scheduler do the garbage collector
        quant = self.env["stock.quant"].search(
            [("product_id", "=", self.product.id), ("location_id", "=", location.id)]
        )
        self.assertTrue(quant)
        self.assertEqual(0.0, quant.quantity)
        self.assertFalse(location.location_will_contain_product_ids)

    def test_will_contain_lot_ids(self):
        location = self.pallets_bin_1_location
        location.computed_storage_category_id.allow_new_product = "same_lot"
        lot_values = {"product_id": self.product.id, "company_id": self.env.company.id}
        lot1 = self.env["stock.lot"].create(lot_values)
        lot2 = self.env["stock.lot"].create(lot_values)

        self._update_qty_in_location(location, self.product, 10, lot=lot1)
        self.assertEqual(location.location_will_contain_lot_ids, lot1)

        # the moves and move lines created are not really valid, but we don't care,
        # its only to have "pending_in_move[_line]_ids" on the location
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
                "quantity": 10,
                "move_id": ml_move.id,
                "company_id": self.env.company.id,
            }
        )
        self.assertEqual(location.location_will_contain_lot_ids, lot1 | lot2)

        location.computed_storage_category_id.allow_new_product = "mixed"
        self.assertEqual(
            location.location_will_contain_lot_ids,
            self.env["stock.lot"].browse(),
        )

    def test_will_contain_product_lot_ids_quantity(self):
        """
        Put a product quantity lot in pallet bin 1 location
        Create a move that will void that location
        Transfer the quantity
        Odoo lets a quant with zero quantity
        The location_will_contain_product_ids should be void
        """
        location = self.pallets_bin_1_location
        location.computed_storage_category_id.allow_new_product = "same_lot"

        lot_values = {"product_id": self.product.id, "company_id": self.env.company.id}
        lot1 = self.env["stock.lot"].create(lot_values)

        self._update_qty_in_location(location, self.product, 10, lot=lot1)
        self.assertEqual(location.location_will_contain_lot_ids, lot1)
        ml_move = self.env["stock.move"].create(
            {
                "name": "test",
                "product_id": self.product.id,
                "location_id": location.id,
                "location_dest_id": self.env.ref("stock.stock_location_customers").id,
                "product_uom": self.product.uom_id.id,
                "product_uom_qty": 10,
            }
        )
        ml_move._action_confirm()
        ml_move._action_assign()

        ml_move.picked = True
        ml_move._action_done()
        # Odoo lets a zero quantity quant before scheduler do the garbage collector
        quant = self.env["stock.quant"].search(
            [("product_id", "=", self.product.id), ("location_id", "=", location.id)]
        )
        self.assertTrue(quant)
        self.assertEqual(0.0, quant.quantity)
        self.assertFalse(location.location_will_contain_lot_ids)

    def test_location_is_empty_non_internal(self):
        location = self.env.ref("stock.stock_location_customers")
        # we always consider an non-internal location empty, the put-away
        # rules do not apply and we can add as many quants as we want
        self.assertTrue(location.location_is_empty)
        self._update_qty_in_location(location, self.product, 10)
        self.assertTrue(location.location_is_empty)

    def test_location_is_empty(self):
        location = self.pallets_reserve_bin_1_location
        self.assertTrue(location.only_empty)
        self.assertTrue(location.location_is_empty)
        self._update_qty_in_location(location, self.product, 10)
        self.assertFalse(location.location_is_empty)

        # When the location has no "only_empty" rule, we don't
        # care about if it is empty or not, we keep it as True so we
        # can always put things inside. Not computing it prevents
        # useless race conditions on concurrent writes.
        category = location.computed_storage_category_id
        category.allow_new_product_ids.filtered(
            lambda rule: rule.allow_new_product == "empty"
        ).allow_new_product = "mixed"
        self.assertTrue(location.location_is_empty)
