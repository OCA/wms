# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields

from odoo.addons.sale_stock_release_channel_partner_by_date.tests.common import (
    SaleReleaseChannelCase,
)


class TestSaleReleaseChannel(SaleReleaseChannelCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.carrier = cls.env.ref("delivery.delivery_carrier")
        cls.carrier2 = cls.env.ref("delivery.delivery_local_delivery")
        cls.carrier_channel = cls.default_channel.copy(
            {
                "name": "Test with carrier",
                "sequence": 10,
                "carrier_ids": [(6, 0, cls.carrier.ids)],
            }
        )
        cls.carrier_channel.action_wake_up()

    def test_sale_order_with_wrong_carrier(self):
        delivery_date = fields.Datetime.now()
        channel_date_model = self.env["stock.release.channel.partner.date"]
        channel_date_model.create(
            {
                "partner_id": self.customer.id,
                "release_channel_id": self.carrier_channel.id,
                "date": delivery_date.date(),
            }
        )
        # With wrong carrier set: order doesn't detect the specific channel for carrier
        order = self._create_sale_order(date=delivery_date)
        order.carrier_id = self.carrier2
        self.assertFalse(order.release_channel_id)
        order.action_confirm()
        self.assertFalse(order.release_channel_id)
        self.assertFalse(order._get_release_channel_partner_date())
        picking_out = order.picking_ids
        self.assertFalse(picking_out.release_channel_id)
        # Then delivery gets the default channel
        self.env["stock.release.channel"].assign_release_channel(picking_out)
        self.assertEqual(picking_out.release_channel_id, self.default_channel)

    def test_sale_order_with_carrier(self):
        delivery_date = fields.Datetime.now()
        channel_date_model = self.env["stock.release.channel.partner.date"]
        channel_date = channel_date_model.create(
            {
                "partner_id": self.customer.id,
                "release_channel_id": self.carrier_channel.id,
                "date": delivery_date.date(),
            }
        )
        # With carrier set: order detects the specific channel for carrier
        order = self._create_sale_order(date=delivery_date)
        order.carrier_id = self.carrier
        self.assertEqual(order.release_channel_id, self.carrier_channel)
        self.assertEqual(order._get_release_channel_partner_date(), channel_date)
        order.action_confirm()
        self.assertEqual(order.release_channel_id, self.carrier_channel)
        self.assertEqual(order._get_release_channel_partner_date(), channel_date)
        picking_out = order.picking_ids
        self.assertFalse(picking_out.release_channel_id)
        # Then delivery gets the default channel
        self.env["stock.release.channel"].assign_release_channel(picking_out)
        self.assertEqual(picking_out.release_channel_id, self.carrier_channel)
