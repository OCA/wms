# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from .common import BlockReleaseCommon


class TestBlockRelease(BlockReleaseCommon):
    def test_release_blocked_policy_direct(self):
        picking = self._out_picking(
            self._create_picking_chain(
                self.wh,
                [(self.product1, 3), (self.product2, 5)],
            )
        )
        picking.release_policy = "direct"  # Default
        self._update_qty_in_location(self.loc_bin1, self.product1, 3.0)
        self._update_qty_in_location(self.loc_bin1, self.product2, 5.0)
        # Moves are ready to be released, nothing is blocked
        self.assertTrue(picking.move_ids[0].release_ready)
        self.assertTrue(picking.move_ids[1].release_ready)
        self.assertTrue(picking.need_release)
        self.assertTrue(picking.release_ready)
        self.assertFalse(picking.release_blocked)
        # Block one of the move: the transfer is still ready to be released and
        # not considered blocked as it remains one move ready
        picking.move_ids[0].action_block_release()
        self.assertFalse(picking.move_ids[0].release_ready)
        self.assertTrue(picking.move_ids[1].release_ready)
        self.assertTrue(picking.need_release)
        self.assertTrue(picking.release_ready)
        self.assertFalse(picking.release_blocked)
        # Block the remaining move: the transfer is not release ready anymore
        # and is considered blocked as well
        picking.move_ids[1].action_block_release()
        self.assertFalse(picking.move_ids[0].release_ready)
        self.assertFalse(picking.move_ids[1].release_ready)
        self.assertTrue(picking.need_release)
        self.assertFalse(picking.release_ready)
        self.assertTrue(picking.release_blocked)
        # Unblock it
        picking.action_unblock_release()
        self.assertTrue(picking.move_ids[0].release_ready)
        self.assertTrue(picking.move_ids[1].release_ready)
        self.assertTrue(picking.need_release)
        self.assertTrue(picking.release_ready)
        self.assertFalse(picking.release_blocked)

    def test_release_blocked_policy_one(self):
        picking = self._out_picking(
            self._create_picking_chain(
                self.wh,
                [(self.product1, 3), (self.product2, 5)],
            )
        )
        picking.release_policy = "one"
        self._update_qty_in_location(self.loc_bin1, self.product1, 3.0)
        self._update_qty_in_location(self.loc_bin1, self.product2, 5.0)
        # Moves are ready to be released, nothing is blocked
        self.assertTrue(picking.move_ids[0].release_ready)
        self.assertTrue(picking.move_ids[1].release_ready)
        self.assertTrue(picking.need_release)
        self.assertTrue(picking.release_ready)
        self.assertFalse(picking.release_blocked)
        # Block one of the move: the transfer is not ready to be released and
        # considered blocked because of the release policy
        picking.move_ids[0].action_block_release()
        self.assertFalse(picking.move_ids[0].release_ready)
        self.assertTrue(picking.move_ids[1].release_ready)
        self.assertTrue(picking.need_release)
        self.assertFalse(picking.release_ready)
        self.assertTrue(picking.release_blocked)
        # Block the remaining move: the transfer is still not release ready
        # and is considered blocked as well
        picking.move_ids[1].action_block_release()
        self.assertFalse(picking.move_ids[0].release_ready)
        self.assertFalse(picking.move_ids[1].release_ready)
        self.assertTrue(picking.need_release)
        self.assertFalse(picking.release_ready)
        self.assertTrue(picking.release_blocked)
        # Unblock it
        picking.action_unblock_release()
        self.assertTrue(picking.move_ids[0].release_ready)
        self.assertTrue(picking.move_ids[1].release_ready)
        self.assertTrue(picking.need_release)
        self.assertTrue(picking.release_ready)
        self.assertFalse(picking.release_blocked)

    def test_block_release_allowed(self):
        picking = self._out_picking(
            self._create_picking_chain(
                self.wh,
                [(self.product1, 3), (self.product2, 5)],
            )
        )
        # We can block the release even if the transfer is not ready
        self.assertTrue(picking.need_release)
        self.assertFalse(picking.release_ready)
        self.assertTrue(picking.block_release_allowed)
        # If moves do not need to be released, we cannot block the transfer
        picking.move_ids.need_release = False
        self.assertFalse(picking.block_release_allowed)

    def test_autoblock_release_on_backorder(self):
        self.wh.delivery_route_id.autoblock_release_on_backorder = True
        picking = self._out_picking(
            self._create_picking_chain(
                self.wh,
                [(self.product1, 3), (self.product2, 5)],
            )
        )
        # Put stock only for the first product/move
        self._update_qty_in_location(self.loc_bin1, self.product1, 3.0)
        # Validate the first move to get a backorder
        move = picking.move_ids[0]
        move.quantity_done = move.product_uom_qty
        picking.move_ids._action_done()
        backorder = picking.backorder_ids
        # Backorder is not release ready and is automatically blocked
        self.assertFalse(backorder.release_ready)
        self.assertTrue(backorder.release_blocked)
