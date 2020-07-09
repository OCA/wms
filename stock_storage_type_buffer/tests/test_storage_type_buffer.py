# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

from odoo.addons.stock_storage_type.tests.common import TestStorageTypeCommon


class TestStorageTypeBuffer(TestStorageTypeCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # when this buffer is not empty, it will block
        # all the pallets locations
        cls.buffer_location = cls.env["stock.location"].create(
            {"name": "Pallet Buffer", "location_id": cls.warehouse.lot_stock_id.id}
        )

        cls.env["stock.location.storage.buffer"].create(
            {
                "buffer_location_ids": [(6, 0, cls.buffer_location.ids)],
                "location_ids": [(6, 0, cls.pallets_location.ids)],
            }
        )

    def _create_pallet_move_to_putaway(self):
        move = self._create_single_move(self.product)
        move._assign_picking()
        package = self.env["stock.quant.package"].create(
            {"product_packaging_id": self.product_pallet_product_packaging.id}
        )
        self._update_qty_in_location(
            move.location_id, move.product_id, move.product_qty, package=package
        )
        return move

    def test_buffer_with_capacity(self):
        """The buffer is empty so we can move to the pallet locations"""
        move = self._create_pallet_move_to_putaway()
        move._action_assign()
        move_line = move.move_line_ids
        # the buffer is available, so we can move the pallet in the pallets locations
        self.assertIn(
            move_line.location_dest_id, self.pallets_location.leaf_location_ids
        )

    def test_buffer_without_capacity_quant(self):
        """The buffer is occupied so we cannot move to the pallet locations

        This test puts a quant in the buffer location.
        """
        move = self._create_pallet_move_to_putaway()

        # put anything in the buffer
        self._update_qty_in_location(self.buffer_location, self.product, 1)

        move._action_assign()
        move_line = move.move_line_ids
        # as the buffer is occupied, the move line can't reach the pallets
        # locations
        self.assertNotIn(
            move_line.location_dest_id, self.pallets_location.leaf_location_ids
        )
        self.assertIn(
            move_line.location_dest_id, self.pallets_reserve_location.leaf_location_ids
        )

    def test_buffer_without_capacity_move_line_dest(self):
        """The buffer is occupied so we cannot move to the pallet locations

        There is no quant in the buffer location in this test, but another
        move line has the buffer as destination.
        """
        other_move = self._create_single_move(self.product)
        other_move._assign_picking()
        self._update_qty_in_location(
            other_move.location_id, other_move.product_id, other_move.product_qty
        )
        other_move._action_assign()
        other_move.move_line_ids.location_dest_id = self.buffer_location

        move = self._create_pallet_move_to_putaway()
        move._action_assign()
        move_line = move.move_line_ids
        # as the buffer will be occupied, the move line can't reach the pallets
        # locations
        self.assertNotIn(
            move_line.location_dest_id, self.pallets_location.leaf_location_ids
        )
        self.assertIn(
            move_line.location_dest_id, self.pallets_reserve_location.leaf_location_ids
        )
