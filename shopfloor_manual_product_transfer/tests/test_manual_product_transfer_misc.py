# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from .test_manual_product_transfer_base import ManualProductTransferCommonCase


class ManualProductTransferMisc(ManualProductTransferCommonCase):
    """Test helper methods used in the manual product transfer scenario."""

    def test_get_product_qty(self):
        # 1. simple case
        qty = self.service._get_product_qty(self.src_location, self.product_a)
        self.assertEqual(qty, 10)
        # 2. with some qties reserved: returns the qty available without reservation
        picking = self._create_picking(lines=[(self.product_a, 4)], confirm=True)
        picking.action_assign()
        qty = self.service._get_product_qty(
            self.src_location, self.product_a, free=True
        )
        self.assertEqual(qty, 6)

    def test_get_product_qty_processed(self):
        # No qty processed at first
        qty = self.service._get_product_qty_processed(self.src_location, self.product_a)
        self.assertEqual(qty, 0)
        # Process some qties (without validation) and check the qty processed
        picking = self._create_picking(lines=[(self.product_a, 10)], confirm=True)
        picking.action_assign()
        picking.move_line_ids.qty_done = 8
        qty = self.service._get_product_qty_processed(self.src_location, self.product_a)
        self.assertEqual(qty, 8)

    def test_get_initial_qty(self):
        # 1. simple case
        qty = self.service._get_initial_qty(self.src_location, self.product_a)
        self.assertEqual(qty, 10)
        # 2. with some qties reserved and "Allow to process reserved quantities"
        #    option disabled: returns the qty available without reservation
        picking = self._create_picking(lines=[(self.product_a, 4)], confirm=True)
        picking.action_assign()
        qty = self.service._get_initial_qty(self.src_location, self.product_a)
        self.assertEqual(qty, 6)
        # 3. with some qties reserved and "Allow to process reserved quantities"
        #    option enabled: returns the qty available reservation included
        self.menu.sudo().allow_unreserve_other_moves = True
        qty = self.service._get_initial_qty(self.src_location, self.product_a)
        self.assertEqual(qty, 10)
