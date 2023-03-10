# Copyright 2020 Camptocamp (https://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import _, exceptions

from .common import ChannelReleaseCase


class TestChannelReleaseBatch(ChannelReleaseCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pickings = cls.picking + cls.picking2 + cls.picking3
        for __ in range(3):
            delivery = cls._out_picking(
                cls._create_picking_chain(
                    cls.wh, [(cls.product1, 5), (cls.product2, 5)], move_type="direct"
                )
            )
            delivery.partner_id = cls.other_partner
            cls.pickings += delivery
        cls._update_qty_in_location(cls.loc_bin1, cls.product1, 1000.0)
        cls._update_qty_in_location(cls.loc_bin1, cls.product2, 1000.0)

    def test_release_auto_forbidden(self):
        self.channel.release_forbidden = True
        with self.assertRaises(exceptions.UserError):
            self.channel.release_next_batch()

    def test_release_auto_max_next_batch_no_config(self):
        self.channel.max_auto_release = 0
        with self.assertRaises(exceptions.UserError):
            self.channel.release_next_batch()

    def test_release_auto_max_next_batch(self):
        self.channel.max_auto_release = 2
        self.channel.release_next_batch()
        # 2 have been released
        self.assertEqual(
            self.pickings.mapped("need_release"), [False, False, True, True, True, True]
        )

        with self.assertRaises(exceptions.UserError):
            # nothing new to release
            self.channel.release_next_batch()

        self._action_done_picking(self.pickings[0].move_lines.move_orig_ids.picking_id)
        self._action_done_picking(self.pickings[0])

        self.channel.release_next_batch()
        # 1 have been released to reach the max of  2
        self.assertEqual(
            self.pickings.mapped("need_release"),
            [False, False, False, True, True, True],
        )

    def test_release_auto_max_no_next_batch(self):
        self.pickings.need_release = False  # cheat for getting the right condition
        action = self.channel.release_next_batch()
        self._assert_action_nothing_in_the_queue(action)

    def test_release_auto_group_commercial_partner(self):
        self.channel.auto_release = "group_commercial_partner"
        self.channel.release_next_batch()
        self.assertFalse(self.picking.need_release)
        self.assertFalse(self.picking2.need_release)
        other_pickings = self.pickings - (self.picking | self.picking2)
        self.assertTrue(all(p.need_release) for p in other_pickings)

    def test_release_auto_group_commercial_partner_no_next_batch(self):
        self.channel.auto_release = "group_commercial_partner"
        self.pickings.need_release = False  # cheat for getting the right condition
        action = self.channel.release_next_batch()
        self._assert_action_nothing_in_the_queue(action)

    def _assert_action_nothing_in_the_queue(self, action):
        self.assertEqual(
            action,
            {
                "effect": {
                    "fadeout": "fast",
                    "message": _("Nothing in the queue!"),
                    "img_url": "/web/static/src/img/smile.svg",
                    "type": "rainbow_man",
                }
            },
        )
