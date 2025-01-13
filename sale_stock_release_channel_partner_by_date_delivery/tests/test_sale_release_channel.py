# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields
from odoo.tests.common import Form

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
        cls.carrier2_channel = cls.default_channel.copy(
            {
                "name": "Test with carrier2",
                "sequence": 10,
                "carrier_ids": [(6, 0, cls.carrier2.ids)],
            }
        )
        cls.carrier2_channel.action_wake_up()

    def test_sale_order_without_carrier_with_channel_date(self):
        delivery_date = fields.Datetime.now()
        # Create one specific channel not matching the SO regarding the carrier
        channel_date_model = self.env["stock.release.channel.partner.date"]
        channel_date_model.create(
            {
                "partner_id": self.customer.id,
                "release_channel_id": self.carrier_channel.id,
                "date": delivery_date.date(),
            }
        )
        order = self._create_sale_order(date=delivery_date)
        self.assertFalse(order.carrier_id)
        self.assertFalse(order.release_channel_id)
        order.action_confirm()
        self.assertFalse(order.release_channel_id)
        self.assertFalse(order._get_release_channel_partner_date())
        picking_out = order.picking_ids
        self.assertFalse(picking_out.release_channel_id)
        # Then delivery gets the default channel
        self.env["stock.release.channel"].assign_release_channel(picking_out)
        self.assertEqual(picking_out.release_channel_id, self.default_channel)

    def test_sale_order_with_carrier_with_channel_date(self):
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

    def test_sale_order_with_carrier_without_channel_date(self):
        delivery_date = fields.Datetime.now()
        # With carrier set: order doesn't detect any specific channel
        order = self._create_sale_order(date=delivery_date)
        order.carrier_id = self.carrier
        self.assertFalse(order.release_channel_id)
        self.assertFalse(order._get_release_channel_partner_date())
        # The user is able to set a release channel on the form
        with Form(order) as form:
            form.release_channel_id = self.carrier_channel
        order.action_confirm()
        self.assertEqual(order.release_channel_id, self.carrier_channel)
        # A specific channel has been created at order confirmation
        self.assertTrue(order._get_release_channel_partner_date())
        picking_out = order.picking_ids
        self.assertFalse(picking_out.release_channel_id)
        # Then delivery then gets the channel defined on the SO
        self.env["stock.release.channel"].assign_release_channel(picking_out)
        self.assertEqual(picking_out.release_channel_id, self.carrier_channel)

    def test_sale_order_with_incompatible_channel_and_carrier_1(self):
        # Case 1: a release channel having a specific channel configured
        # is detected, but incompatible with the selected carrier afterwards.
        #   => unset the detected release channel
        delivery_date = fields.Datetime.now()
        channel_date_model = self.env["stock.release.channel.partner.date"]
        channel_date_model.create(
            {
                "partner_id": self.customer.id,
                "release_channel_id": self.carrier_channel.id,
                "date": delivery_date.date(),
            }
        )
        order = self._create_sale_order(
            date=delivery_date, channel=self.carrier_channel
        )
        self.assertEqual(order.release_channel_id, self.carrier_channel)
        #   => select a carrier
        order.carrier_id = self.carrier2
        self.assertFalse(order.release_channel_id)
        # Confirm the order and check release channel on delivery
        order.action_confirm()
        self.assertFalse(order.release_channel_id)
        self.assertFalse(order._get_release_channel_partner_date())
        picking_out = order.picking_ids
        self.assertFalse(picking_out.release_channel_id)
        # Then delivery gets the default channel
        self.env["stock.release.channel"].assign_release_channel(picking_out)
        self.assertEqual(picking_out.release_channel_id, self.default_channel)

    def test_sale_order_with_incompatible_channel_and_carrier_2(self):
        # Case 2: a release channel having a specific channel configured
        # is detected, but incompatible with the selected carrier afterwards.
        # However another specific channel is compatible with the selected carrier.
        #   => update the selected release channel to be compatible with the
        #   selected carrier
        delivery_date = fields.Datetime.now()
        channel_date_model = self.env["stock.release.channel.partner.date"]
        channel_date_model.create(
            {
                "partner_id": self.customer.id,
                "release_channel_id": self.carrier_channel.id,
                "date": delivery_date.date(),
            }
        )
        order = self._create_sale_order(
            date=delivery_date, channel=self.carrier_channel
        )
        self.assertEqual(order.release_channel_id, self.carrier_channel)
        channel_date_model = self.env["stock.release.channel.partner.date"]
        channel_date = channel_date_model.create(
            {
                "partner_id": self.customer.id,
                "release_channel_id": self.carrier2_channel.id,
                "date": delivery_date.date(),
            }
        )
        #   => select a carrier
        order.carrier_id = self.carrier2
        self.assertEqual(order.release_channel_id, self.carrier2_channel)
        # Confirm the order and check release channel on delivery
        order.action_confirm()
        self.assertEqual(order.release_channel_id, self.carrier2_channel)
        self.assertEqual(order._get_release_channel_partner_date(), channel_date)
        picking_out = order.picking_ids
        self.assertFalse(picking_out.release_channel_id)
        # Then delivery gets the selected channel
        self.env["stock.release.channel"].assign_release_channel(picking_out)
        self.assertEqual(picking_out.release_channel_id, self.carrier2_channel)
