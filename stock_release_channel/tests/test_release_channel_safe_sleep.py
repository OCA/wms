# Copyright 2025 ACSONE SA/NV (https://acsone.eu)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)


from .common import ReleaseChannelCase


class TestReleaseChannelCancel(ReleaseChannelCase):
    def test_release_channel_cancel(self):
        """
        Create a new channel with a priority filter
        Release the move with that picking priority

        The created channel is assigned to the move picking

        Call the unassign on the channel and check the
        picking is unassigned

        Set the channel to 'asleep' state
        Try to assign the picking

        The default channel should be set
        """
        self.env.company.recompute_channel_on_pickings_at_release = True
        channel = self._create_channel(
            name="Test Domain",
            sequence=1,
            rule_domain=[("priority", "=", "1")],
        )
        move = self._create_single_move(self.product1, 10)
        move.picking_id.priority = "1"
        move.release_available_to_promise()
        self.assertEqual(move.picking_id.release_channel_id, channel)

        channel.action_safe_sleep()
        self.assertFalse(move.picking_id.release_channel_id)

        move.release_available_to_promise()
        self.assertEqual(move.picking_id.release_channel_id, self.default_channel)

    def test_release_channel_cancel_after_picking(self):
        """
        Create a new channel with a priority filter
        Release the move with that picking priority

        The created channel is assigned to the move picking

        Transfer the picking from stock location

        Call the unassign on the channel and check the
        picking is unassigned

        Set the channel to 'asleep' state
        Try to assign the picking

        The default channel should be set

        Transfer the outgoing picking

        Try to unassign it. It should be impossible

        """
        self.env.company.recompute_channel_on_pickings_at_release = True
        channel = self._create_channel(
            name="Test Domain",
            sequence=1,
            rule_domain=[("priority", "=", "1")],
        )
        self._update_qty_in_location(self.wh.lot_stock_id, self.product1, 10.0)
        move = self._create_single_move(self.product1, 10)
        move.warehouse_id = self.wh
        move.procure_method = "make_to_order"
        move.rule_id = self.wh.delivery_route_id.rule_ids.filtered(
            lambda rule: rule.location_dest_id == move.location_dest_id
        )
        move.route_ids = move.rule_id.route_id
        move.picking_id.priority = "1"
        move.need_release = True
        move.invalidate_cache(["ordered_available_to_promise_qty"])
        move.release_available_to_promise()
        self.assertEqual(move.picking_id.release_channel_id, channel)

        self.assertTrue(move.move_orig_ids)

        move.move_orig_ids.quantity_done = 10.0
        move.move_orig_ids._action_done()

        channel.action_safe_sleep()
        self.assertFalse(move.picking_id.release_channel_id)

        move.release_available_to_promise()
        self.assertEqual(move.picking_id.release_channel_id, self.default_channel)

        move.quantity_done = 10.0
        move._action_done()
        self.assertEqual("done", move.state)
