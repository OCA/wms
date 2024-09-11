# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields

from .common import SaleReleaseChannelCase


class TestSaleReleaseChannel(SaleReleaseChannelCase):
    def test_sale_release_channel_auto(self):
        # Without channel: delivery gets automatically the default release channel
        order_auto_channel = self._create_sale_order()
        self.assertFalse(order_auto_channel.release_channel_id)
        order_auto_channel.action_confirm()
        self.assertFalse(order_auto_channel.release_channel_id)
        self.assertFalse(order_auto_channel._get_release_channel_partner_date())
        picking_out = order_auto_channel.picking_ids
        self.assertFalse(picking_out.release_channel_id)
        self.env["stock.release.channel"].assign_release_channel(picking_out)
        self.assertEqual(picking_out.release_channel_id, self.default_channel)

    def test_sale_force_release_channel(self):
        # Force the channel on order
        order = self._create_sale_order(channel=self.test_channel)
        self.assertEqual(order.release_channel_id, self.test_channel)
        channel_date = order._get_release_channel_partner_date()
        self.assertFalse(channel_date)
        order.action_confirm()
        channel_date = order._get_release_channel_partner_date()
        self.assertTrue(channel_date)
        # Specific release channel is set by the channel assignment mechanism
        picking_out = order.picking_ids
        self.assertFalse(picking_out.release_channel_id)
        self.env["stock.release.channel"].assign_release_channel(picking_out)
        self.assertEqual(picking_out.release_channel_id, self.test_channel)
        # Cancelling the order removes the specific channel entry
        order.with_context(disable_cancel_warning=True).action_cancel()
        channel_date = order._get_release_channel_partner_date()
        self.assertFalse(channel_date)

    def test_sale_computed_release_channel(self):
        # Create a specific channel entry from an order, and check if it is
        # automatically used by a second order with the same delivery date.
        now = fields.Datetime.now()
        order1 = self._create_sale_order(channel=self.test_channel, date=now)
        self.assertEqual(order1.release_channel_id, self.test_channel)
        channel_date = order1._get_release_channel_partner_date()
        self.assertFalse(channel_date)
        order1.action_confirm()
        channel_date = order1._get_release_channel_partner_date()
        self.assertTrue(channel_date)
        # Create the second order with the same delivery date
        order2 = self._create_sale_order(date=now)
        self.assertEqual(order2.release_channel_id, self.test_channel)
        channel_date = order2._get_release_channel_partner_date()
        self.assertEqual(channel_date.release_channel_id, order2.release_channel_id)
        order2.action_confirm()
        channel_date = order2._get_release_channel_partner_date()
        self.assertEqual(channel_date.release_channel_id, order2.release_channel_id)

    def test_sale_cancel_unlink_channel_date(self):
        # Create a specific channel entry on 1st order
        now = fields.Datetime.now()
        order1 = self._create_sale_order(channel=self.test_channel, date=now)
        order1.action_confirm()
        channel_date = order1._get_release_channel_partner_date()
        # Create a 2nd order that matches the specific channel entry
        order2 = self._create_sale_order(date=now)
        order2.action_confirm()
        self.assertEqual(order2._get_release_channel_partner_date(), channel_date)
        # Cancel the 1st order: the specific channel entry is preserved
        order1._action_cancel()
        self.assertTrue(channel_date.exists())
        # Cancel the 2nd (and last) order: the specific channel entry is removed
        order2._action_cancel()
        self.assertFalse(channel_date.exists())

    def test_sale_different_warehouses(self):
        # Create 1st order on default warehouse
        now = fields.Datetime.now()
        order1 = self._create_sale_order(channel=self.test_channel, date=now)
        wh = order1.warehouse_id
        order1.action_confirm()
        channel_date = order1._get_release_channel_partner_date()
        # Create 2nd order on another warehouse
        wh2 = wh.copy({"name": "2nd WH", "code": "WH2"})
        order2 = self._create_sale_order(date=now, warehouse=wh2)
        # Specific channel entry matches the 1st order as the underlying release
        # channel is not restricted on a given warehouse
        self.assertEqual(order2._get_release_channel_partner_date(), channel_date)
        # Restrict the release channel to the 1st warehouse: no specific channel
        # entry is found
        channel_date.release_channel_id.warehouse_id = wh
        self.assertFalse(order2._get_release_channel_partner_date())
