# Copyright 2020 Camptocamp (https://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from datetime import timedelta

from odoo import exceptions, fields

from .common import ChannelReleaseCase


class TestChannelAction(ChannelReleaseCase):
    def _assert_picking_action(self, action, pickings, context=None):
        self.assertEqual(action["domain"][0][0], "id")
        self.assertEqual(action["domain"][0][1], "in")
        self.assertEqual(set(action["domain"][0][2]), set(pickings.ids))

    def _assert_move_action(self, action, pickings, context=None):
        self.assertEqual(action["domain"][0][0], "picking_id")
        self.assertEqual(action["domain"][0][1], "in")
        self.assertEqual(set(action["domain"][0][2]), set(pickings.ids))
        self.assertEqual(action["context"], context or {})

    def test_action_all(self):
        self._assert_picking_action(
            self.channel.action_picking_all(),
            self.picking + self.picking2 + self.picking3,
            {"search_default_release_ready": 1},
        )
        self._assert_move_action(
            self.channel.action_move_all(),
            self.picking + self.picking2 + self.picking3,
            {"search_default_release_ready": 1},
        )

    def test_action_release_forbidden(self):
        self.channel.release_forbidden = True
        with self.assertRaises(exceptions.UserError):
            self.picking.release_available_to_promise()
        self.channel.release_forbidden = False
        self.picking.release_available_to_promise()

    def test_action_release_ready(self):
        self._update_qty_in_location(self.loc_bin1, self.product1, 10.0)
        self._update_qty_in_location(self.loc_bin1, self.product2, 10.0)

        self._assert_picking_action(
            self.channel.action_picking_release_ready(), self.picking + self.picking2
        )
        self._assert_move_action(
            self.channel.action_move_release_ready(), self.picking + self.picking2
        )

    def test_action_released_assigned_waiting(self):
        self._update_qty_in_location(self.loc_bin1, self.product1, 10.0)
        self._update_qty_in_location(self.loc_bin1, self.product2, 10.0)
        self.picking.release_available_to_promise()
        self.picking2.release_available_to_promise()

        self._assert_picking_action(
            self.channel.action_picking_released(), self.picking + self.picking2
        )
        self._assert_move_action(
            self.channel.action_move_released(), self.picking + self.picking2
        )

        pick_picking = self.picking.move_ids.move_orig_ids.picking_id
        self._action_done_picking(pick_picking)

        self._assert_picking_action(
            self.channel.action_picking_assigned(), self.picking
        )
        self._assert_move_action(self.channel.action_move_assigned(), self.picking)

        self._assert_picking_action(
            self.channel.action_picking_waiting(), self.picking2
        )
        self._assert_move_action(self.channel.action_move_waiting(), self.picking2)

    def _release_all(self):
        self._update_qty_in_location(self.loc_bin1, self.product1, 15.0)
        self._update_qty_in_location(self.loc_bin1, self.product2, 15.0)
        (self.picking + self.picking2 + self.picking3).release_available_to_promise()

    def test_action_all_related(self):
        self._release_all()
        pickings = self.picking + self.picking2 + self.picking3
        related = pickings.move_ids.move_orig_ids.picking_id

        action = self.channel.action_picking_all_related()
        self._assert_picking_action(
            action,
            related,
            {"search_default_available": 1, "search_default_picking_type": 1},
        )

    def test_action_late(self):
        self._release_all()
        self.picking.scheduled_date = fields.Datetime.now() - timedelta(hours=1)
        self.picking2.scheduled_date = fields.Datetime.now() - timedelta(hours=1)
        self._assert_picking_action(
            self.channel.action_picking_late(), self.picking + self.picking2
        )
        self._assert_move_action(
            self.channel.action_move_late(), self.picking + self.picking2
        )

    def test_action_priority(self):
        self._release_all()
        self.picking.priority = "1"
        self.picking2.priority = "1"
        self._assert_picking_action(
            self.channel.action_picking_priority(), self.picking + self.picking2
        )
        self._assert_move_action(
            self.channel.action_move_priority(), self.picking + self.picking2
        )

    def test_action_done(self):
        self._release_all()
        self._action_done_picking(self.picking.move_ids.move_orig_ids.picking_id)
        self._action_done_picking(self.picking)

        self._assert_picking_action(self.channel.action_picking_done(), self.picking)
        self._assert_move_action(self.channel.action_move_done(), self.picking)

    def test_action_no_last_picking_done(self):
        with self.assertRaises(exceptions.UserError):
            self.channel.get_action_picking_form()

    def test_action_last_picking_done(self):
        self._release_all()
        self._action_done_picking(self.picking.move_ids.move_orig_ids.picking_id)
        self._action_done_picking(self.picking)
        action = self.channel.get_action_picking_form()
        self.assertEqual(action["res_id"], self.picking.id)
