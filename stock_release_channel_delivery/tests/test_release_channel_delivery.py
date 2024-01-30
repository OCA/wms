# Copyright 2020 Camptocamp (https://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)


from odoo.addons.stock_release_channel.tests.common import ReleaseChannelCase


class TestReleaseChannel(ReleaseChannelCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.carrier = cls.env.ref("delivery.free_delivery_carrier")
        cls.carrier2 = cls.carrier.copy({})
        cls.channel = cls.env.ref("stock_release_channel.stock_release_channel_default")
        cls.move = cls._create_single_move(cls.product1, 10)
        cls.picking = cls.move.picking_id

    def test_00(self):
        """
        picking and release channel have the same carrier
        """
        self.picking.carrier_id = self.carrier
        self.channel.carrier_id = self.carrier
        self.picking.assign_release_channel()
        self.assertEqual(self.picking.release_channel_id, self.channel)

    def test_01(self):
        """
        picking have carrier but not the release channel
        """
        self.picking.carrier_id = self.carrier
        self.channel.carrier_id = False
        self.picking.assign_release_channel()
        self.assertEqual(self.picking.release_channel_id, self.channel)

    def test_02(self):
        """
        picking and release channel have different carrier
        """
        self.picking.carrier_id = self.carrier
        self.channel.carrier_id = self.carrier2
        self.picking.assign_release_channel()
        self.assertFalse(self.picking.release_channel_id)

    def test_03(self):
        """
        picking have no carrier but release channel have one
        """
        self.picking.carrier_id = False
        self.channel.carrier_id = self.carrier
        self.picking.assign_release_channel()
        self.assertFalse(self.picking.release_channel_id)
