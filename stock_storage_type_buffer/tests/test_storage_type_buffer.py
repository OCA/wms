# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from lxml import html

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

        cls.storage_buffer = cls.env["stock.location.storage.buffer"].create(
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

    def test_location_field_is_in_storage_buffer(self):
        self.assertTrue(self.buffer_location.is_in_storage_buffer)

        area = self.env["stock.location"].create(
            {"name": "Pallet Area", "location_id": self.warehouse.lot_stock_id.id}
        )
        self.assertFalse(area.is_in_storage_buffer)
        leaf = self.env["stock.location"].create(
            {"name": "Pallet Leaf", "location_id": area.id}
        )
        self.assertFalse(area.is_in_storage_buffer)

        area.location_id = self.buffer_location.id
        self.assertTrue(area.is_in_storage_buffer)
        self.assertTrue(leaf.is_in_storage_buffer)

        self.storage_buffer.unlink()
        self.assertFalse(self.buffer_location.is_in_storage_buffer)
        self.assertFalse(area.is_in_storage_buffer)
        self.assertFalse(leaf.is_in_storage_buffer)

    def test_location_field_is_empty(self):
        """Do not compute "location_is_empty" if there is no buffer"""
        # we have a buffer on the location: compute location_is_empty
        self.assertTrue(self.buffer_location.location_is_empty)
        self._update_qty_in_location(self.buffer_location, self.product, 1)
        self.assertFalse(self.buffer_location.location_is_empty)
        self.storage_buffer.unlink()
        # when we have no buffer, we don't care about the field
        # "location_is_empty", we prefer not to compute it to prevent
        # concurrent writes
        self.assertTrue(self.buffer_location.location_is_empty)

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

    def test_buffer_name_get(self):
        self.assertEqual(self.storage_buffer.display_name, "Pallet Buffer")

        box_buffer = self.env["stock.location"].create(
            {"name": "Box Buffer", "location_id": self.warehouse.lot_stock_id.id}
        )
        pallet_buffer_2 = self.env["stock.location"].create(
            {"name": "Pallet Buffer 2", "location_id": self.warehouse.lot_stock_id.id}
        )
        pallet_buffer_3 = self.env["stock.location"].create(
            {"name": "Pallet Buffer 3", "location_id": self.warehouse.lot_stock_id.id}
        )
        self.storage_buffer.buffer_location_ids = (
            self.buffer_location + box_buffer + pallet_buffer_2 + pallet_buffer_3
        )
        self.storage_buffer.invalidate_cache(fnames=["display_name"])
        self.assertEqual(
            self.storage_buffer.display_name,
            "Pallet Buffer, Box Buffer, Pallet Buffer 2, ...",
        )

    def test_buffer_help_message_capacity(self):
        expected_result = """
        <span>The buffer locations</span>
        <ul class="mt8">
            <li>
                <span>WH/Stock/Pallet Buffer</span>
            </li>
        </ul>
        <span>
            currently <strong>have capacity</strong>,
            so the following locations
            <strong>can receive putaways</strong>:
        </span>
        <ul class="mt8">
            <li>
                <span>WH/Stock/Pallets storage area/Pallets Bin 1</span>
            </li>
            <li>
                <span>WH/Stock/Pallets storage area/Pallets Bin 2</span>
            </li>
            <li>
                <span>WH/Stock/Pallets storage area/Pallets Bin 3</span>
            </li>
            <li>
                <span>WH/Stock/Pallets storage area/Pallets Bin 4</span>
            </li>
        </ul>
        """
        self.assertEqual(
            html.fromstring(self.storage_buffer.help_message.strip()),
            html.fromstring(expected_result),
        )

    def test_buffer_help_message_no_capacity(self):
        # put anything in the buffer
        self._update_qty_in_location(self.buffer_location, self.product, 1)

        # message should show it has no capacity
        expected_result = """
        <span>The buffer locations</span>
        <ul class="mt8">
            <li>
                <span>WH/Stock/Pallet Buffer</span>
            </li>
        </ul>
        <span>
            currently <strong>have no capacity</strong>,
            so the following locations
            <strong>cannot receive putaways</strong>:
        </span>
        <ul class="mt8">
            <li>
                <span>WH/Stock/Pallets storage area/Pallets Bin 1</span>
            </li>
            <li>
                <span>WH/Stock/Pallets storage area/Pallets Bin 2</span>
            </li>
            <li>
                <span>WH/Stock/Pallets storage area/Pallets Bin 3</span>
            </li>
            <li>
                <span>WH/Stock/Pallets storage area/Pallets Bin 4</span>
            </li>
        </ul>
        <p>
            The buffers have no capacity because they all contain
            goods or will contain goods due to move lines reaching them.
        </p>
        """
        self.assertEqual(
            html.fromstring(self.storage_buffer.help_message.strip()),
            html.fromstring(expected_result),
        )

    def test_buffer_help_message_no_record(self):
        expected_result = (
            "<p>Select buffer locations and locations "
            "blocked for putaways when the buffer locations "
            "already contain goods or have move lines "
            "reaching them.</p>"
        )
        self.storage_buffer.buffer_location_ids = False
        self.assertEqual(
            html.fromstring(self.storage_buffer.help_message.strip()),
            html.fromstring(expected_result),
        )
