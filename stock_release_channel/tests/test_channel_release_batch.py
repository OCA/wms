# Copyright 2020 Camptocamp (https://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import exceptions

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
        self.channel.max_batch_mode = 0
        with self.assertRaises(exceptions.UserError):
            self.channel.release_next_batch()

    def test_release_auto_max_next_batch(self):
        self.channel.max_batch_mode = 2
        self.channel.release_next_batch()
        # 2 have been released
        self.assertEqual(
            self.pickings.mapped("need_release"), [False, False, True, True, True, True]
        )

        with self.assertRaises(exceptions.UserError):
            # nothing new to release
            self.channel.release_next_batch()

        self._action_done_picking(self.pickings[0].move_ids.move_orig_ids.picking_id)
        self._action_done_picking(self.pickings[0])

        self.channel.release_next_batch()
        # 1 have been released to reach the max of  2
        self.assertEqual(
            self.pickings.mapped("need_release"),
            [False, False, False, True, True, True],
        )

    def test_release_auto_max_no_next_batch(self):
        action = self.channel.release_next_batch()
        action = self.channel.release_next_batch()
        self._assert_action_nothing_in_the_queue(action)
