# Copyright 2020 Camptocamp (https://www.camptocamp.com)
# Copyright 2024 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from datetime import timedelta

from odoo import fields

from .common import ChannelReleaseCase


class TestChannelComputedFields(ChannelReleaseCase):
    def test_computed_fields_counts_not_ready(self):
        self.assertEqual(self.channel.count_picking_all, 3)
        self.assertEqual(self.channel.count_move_all, 6)
        self.assertEqual(self.channel.count_picking_release_ready, 0)
        self.assertEqual(self.channel.count_picking_released, 0)
        self.assertEqual(self.channel.count_picking_assigned, 0)
        self.assertEqual(self.channel.count_picking_waiting, 0)
        self.assertEqual(self.channel.count_picking_late, 0)
        self.assertEqual(self.channel.count_picking_priority, 0)
        self.assertEqual(self.channel.count_picking_done, 0)
        self.assertEqual(self.channel.count_picking_chain, 0)
        self.assertEqual(self.channel.count_picking_chain_in_progress, 0)

    def test_computed_fields_counts_release_ready(self):
        self._update_qty_in_location(self.loc_bin1, self.product1, 20.0)
        self._update_qty_in_location(self.loc_bin1, self.product2, 20.0)

        self.assertEqual(self.channel.count_picking_release_ready, 3)

    def test_computed_fields_counts_released(self):
        self._update_qty_in_location(self.loc_bin1, self.product1, 20.0)
        self._update_qty_in_location(self.loc_bin1, self.product2, 20.0)
        self.picking.release_available_to_promise()
        pick_picking = self.picking.move_ids.move_orig_ids.picking_id

        self.assertEqual(self.channel.count_picking_all, 3)
        self.assertEqual(self.channel.count_move_all, 6)
        self.assertEqual(self.channel.count_picking_release_ready, 2)
        self.assertEqual(self.channel.count_move_release_ready, 4)
        self.assertEqual(self.channel.count_picking_released, 1)
        self.assertEqual(self.channel.count_move_released, 2)
        self.assertEqual(self.channel.count_picking_assigned, 0)
        self.assertEqual(self.channel.count_picking_waiting, 1)
        self.assertEqual(self.channel.count_move_waiting, 2)
        self.assertEqual(self.channel.count_picking_late, 0)
        self.assertEqual(self.channel.count_picking_priority, 0)
        self.assertEqual(self.channel.count_picking_done, 0)
        self.assertEqual(self.channel.count_picking_chain, 1)
        self.assertEqual(self.channel.count_picking_chain_in_progress, 1)
        self.assertEqual(self.channel.picking_chain_ids, pick_picking)

    def test_computed_fields_counts_late(self):
        self._update_qty_in_location(self.loc_bin1, self.product1, 20.0)
        self._update_qty_in_location(self.loc_bin1, self.product2, 20.0)
        self.picking.release_available_to_promise()
        # FIXME late should measure late internal operations, not late deliveries
        # pick_picking = self.picking.move_ids.move_orig_ids.picking_id
        # pick_picking.scheduled_date = fields.Datetime.now() - timedelta(hours=1)
        self.picking.scheduled_date = fields.Datetime.now() - timedelta(hours=1)

        self.assertEqual(self.channel.count_picking_late, 1)
        self.assertEqual(self.channel.count_move_late, 2)

    def test_computed_fields_counts_pick_done(self):
        self._update_qty_in_location(self.loc_bin1, self.product1, 20.0)
        self._update_qty_in_location(self.loc_bin1, self.product2, 20.0)
        self.picking.release_available_to_promise()
        pick_picking = self.picking.move_ids.move_orig_ids.picking_id
        self._action_done_picking(pick_picking)

        self.assertEqual(self.channel.count_picking_assigned, 1)
        self.assertEqual(self.channel.count_move_assigned, 2)

    def test_computed_fields_counts_ship_done(self):
        self._update_qty_in_location(self.loc_bin1, self.product1, 20.0)
        self._update_qty_in_location(self.loc_bin1, self.product2, 20.0)
        self.picking.release_available_to_promise()
        pick_picking = self.picking.move_ids.move_orig_ids.picking_id
        self._action_done_picking(pick_picking)
        self._action_done_picking(self.picking)

        self.assertEqual(self.channel.count_picking_done, 1)
        self.assertEqual(self.channel.count_picking_chain, 0)
        self.assertEqual(self.channel.count_picking_chain_in_progress, 0)

        self.assertEqual(self.channel.last_done_picking_id, self.picking)
        self.assertEqual(self.channel.last_done_picking_name, self.picking.name)
        self.assertEqual(
            self.channel.last_done_picking_date_done, self.picking.date_done
        )
