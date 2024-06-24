# Copyright 2020 Camptocamp (https://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from .common import ReleaseChannelCase


class ReleaseChannelPartnerCommon(ReleaseChannelCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "partner"})
        cls.partner_channel = cls._create_channel(
            name="partner channel",
            sequence=20,
            code="pickings = pickings.filtered(lambda p: p.priority == '1')",
        )
        cls.other_channel = cls._create_channel(
            name="Test Domain",
            sequence=10,
            rule_domain=[("priority", "=", "1")],
        )
        cls.move = cls._create_single_move(cls.product1, 10)
        cls.move2 = cls._create_single_move(cls.product2, 10)
        cls.move.picking_id.priority = "1"
        cls.move.picking_id.partner_id = cls.partner
        cls.partner.stock_release_channel_ids = cls.partner_channel
        cls.partner2 = cls.env["res.partner"].create({"name": "partner"})
        cls.move2.picking_id.priority = "1"
        cls.move2.picking_id.partner_id = cls.partner2
        cls.partner2.stock_release_channel_ids = False
        cls.moves = cls.move + cls.move2


class TestReleaseChannelPartner(ReleaseChannelPartnerCommon):
    def test_00(self):
        """partner release channel is higher priority than other channels"""
        self.moves.picking_id.assign_release_channel()
        self.assertEqual(self.move.picking_id.release_channel_id, self.partner_channel)
        self.assertEqual(self.move2.picking_id.release_channel_id, self.other_channel)

    def test_01(self):
        """partner channel is not assigned if isn't active"""
        self.partner_channel.active = False
        self.moves.picking_id.assign_release_channel()
        self.assertEqual(self.move.picking_id.release_channel_id, self.other_channel)
        self.assertEqual(self.move2.picking_id.release_channel_id, self.other_channel)

    def test_02(self):
        """partner channel is not assigned if it's asleep"""
        self.partner_channel.state = "asleep"
        self.moves.picking_id.assign_release_channel()
        self.assertEqual(self.move.picking_id.release_channel_id, self.other_channel)
        self.assertEqual(self.move2.picking_id.release_channel_id, self.other_channel)

    def test_03(self):
        """partner channel is assigned considering the sequence"""
        partner_channel_low_sequence = self._create_channel(
            name="Partner channel",
            sequence=1,
            code="pickings = pickings.filtered(lambda p: p.priority == '1')",
        )
        self.partner.stock_release_channel_ids |= partner_channel_low_sequence
        self.move.picking_id.assign_release_channel()
        self.assertEqual(
            self.move.picking_id.release_channel_id, partner_channel_low_sequence
        )

    def test_04(self):
        """partner channel is assigned considering the sequence"""
        partner_channel_low_sequence = self._create_channel(
            name="Partner channel",
            sequence=1,
            code="pickings = pickings.filtered(lambda p: p.priority == 'x')",
        )
        self.partner.stock_release_channel_ids |= partner_channel_low_sequence
        self.move.picking_id.assign_release_channel()
        self.assertEqual(self.move.picking_id.release_channel_id, self.partner_channel)
