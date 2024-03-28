# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from .common import SaleReleaseChannelCase


class TestSaleReleaseChannel(SaleReleaseChannelCase):
    def test_sale_release_channel(self):
        # Without channel: delivery gets automatically the default release channel
        order_auto_channel = self._create_sale_order()
        order_auto_channel.action_confirm()
        picking_out = order_auto_channel.picking_ids
        self.assertFalse(picking_out.release_channel_id)
        self.env["stock.release.channel"].assign_release_channel(picking_out)
        self.assertEqual(picking_out.release_channel_id, self.default_channel)
        # Force the channel on order
        order_force_channel = self._create_sale_order(channel=self.test_channel)
        order_force_channel.action_confirm()
        picking_out = order_force_channel.picking_ids
        self.assertFalse(picking_out.release_channel_id)
        self.env["stock.release.channel"].assign_release_channel(picking_out)
        self.assertEqual(picking_out.release_channel_id, self.test_channel)
