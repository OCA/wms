# Copyright 2020 Camptocamp (https://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)


from odoo.addons.stock_release_channel.tests.common import ChannelReleaseCase


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

    def test_release_auto_group_commercial_partner(self):
        self.channel.batch_mode = "group_commercial_partner"
        self.channel.release_next_batch()
        self.assertFalse(self.picking.need_release)
        self.assertFalse(self.picking2.need_release)
        other_pickings = self.pickings - (self.picking | self.picking2)
        self.assertTrue(all(p.need_release) for p in other_pickings)

    def test_release_auto_group_commercial_partner_no_next_batch(self):
        self.channel.batch_mode = "group_commercial_partner"
        self.pickings.need_release = False  # cheat for getting the right condition
        action = self.channel.release_next_batch()
        self._assert_action_nothing_in_the_queue(action)
