# Copyright 2020 Camptocamp (https://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from datetime import timedelta

from odoo import fields

from .common import ChannelReleaseCase


class TestChannelComputedFields(ChannelReleaseCase):
    def test_computed_fields_counts(self):
        picking = self.picking
        channel = self.channel

        self.assertEqual(channel.count_picking_all, 3)
        self.assertEqual(channel.count_move_all, 6)
        self.assertEqual(channel.count_picking_release_ready, 0)
        self.assertEqual(channel.count_picking_released, 0)
        self.assertEqual(channel.count_picking_assigned, 0)
        self.assertEqual(channel.count_picking_waiting, 0)
        self.assertEqual(channel.count_picking_late, 0)
        self.assertEqual(channel.count_picking_priority, 0)
        self.assertEqual(channel.count_picking_done, 0)
        self.assertEqual(channel.count_picking_chain, 0)
        self.assertEqual(channel.count_picking_chain_in_progress, 0)

        self._update_qty_in_location(self.loc_bin1, self.product1, 20.0)
        self._update_qty_in_location(self.loc_bin1, self.product2, 20.0)

        channel.env.invalidate_all()
        self.assertEqual(channel.count_picking_release_ready, 3)

        picking.release_available_to_promise()
        pick_picking = picking.move_ids.move_orig_ids.picking_id

        channel.env.invalidate_all()

        self.assertEqual(channel.count_picking_all, 3)
        self.assertEqual(channel.count_move_all, 6)
        self.assertEqual(channel.count_picking_release_ready, 2)
        self.assertEqual(channel.count_move_release_ready, 4)
        self.assertEqual(channel.count_picking_released, 1)
        self.assertEqual(channel.count_move_released, 2)
        self.assertEqual(channel.count_picking_assigned, 0)
        self.assertEqual(channel.count_picking_waiting, 1)
        self.assertEqual(channel.count_move_waiting, 2)
        self.assertEqual(channel.count_picking_late, 0)
        self.assertEqual(channel.count_picking_priority, 0)
        self.assertEqual(channel.count_picking_done, 0)
        self.assertEqual(channel.count_picking_chain, 1)
        self.assertEqual(channel.count_picking_chain_in_progress, 1)
        self.assertEqual(channel.picking_chain_ids, pick_picking)

        picking.scheduled_date = fields.Datetime.now() - timedelta(hours=1)
        channel.env.invalidate_all()
        self.assertEqual(channel.count_picking_late, 1)
        self.assertEqual(channel.count_move_late, 2)

        self._action_done_picking(pick_picking)

        channel.env.invalidate_all()
        self.assertEqual(channel.count_picking_assigned, 1)
        self.assertEqual(channel.count_move_assigned, 2)
        self._action_done_picking(picking)

        channel.env.invalidate_all()
        self.assertEqual(channel.count_picking_done, 1)
        self.assertEqual(channel.count_picking_chain, 0)
        self.assertEqual(channel.count_picking_chain_in_progress, 0)

        self.assertEqual(channel.last_done_picking_id, picking)
        self.assertEqual(channel.last_done_picking_name, picking.name)
        self.assertEqual(channel.last_done_picking_date_done, picking.date_done)
