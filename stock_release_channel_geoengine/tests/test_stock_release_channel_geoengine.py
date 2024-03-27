# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tools import mute_logger

from .common import TestStockReleaseChannelGeoengineCommon


class TestStockReleaseChannelGeoengine(TestStockReleaseChannelGeoengineCommon):
    @mute_logger("odoo.addons.stock_release_channel.models.stock_release_channel")
    def test_assign_based_on_location_1(self):
        """
        test assigning one picking based on location
        """
        self.delivery_address_1.geo_point = self.point1
        self.pickings.assign_release_channel()
        self.assertEqual(self.picking.release_channel_id, self.channel)
        self.assertFalse((self.picking2 | self.picking3).release_channel_id)

    def test_assign_based_on_location_2(self):
        """
        test assigning all picking based on location
        """
        self.delivery_address_1.geo_point = self.point1
        self.delivery_address_2.geo_point = self.point2
        self.other_partner.geo_point = self.point3
        self.pickings.assign_release_channel()
        self.assertEqual(self.picking.release_channel_id, self.channel)
        self.assertEqual(self.picking2.release_channel_id, self.channel)
        self.assertEqual(self.picking3.release_channel_id, self.channel)

    @mute_logger("odoo.addons.stock_release_channel.models.stock_release_channel")
    def test_no_partner_geo_point(self):
        """
        test assigning to release channel without geo-localizing partners
        """
        self.pickings.assign_release_channel()
        self.assertFalse(self.pickings.release_channel_id)

    @mute_logger("odoo.addons.stock_release_channel.models.stock_release_channel")
    def test_partner_not_in_geo_release_channel(self):
        """
        test assigning to release channel a geo-localized partner but marked as not
        in_geo_release_channel
        """
        self.delivery_address_1.geo_point = self.point1
        self.delivery_address_1.in_geo_release_channel = False
        self.pickings.assign_release_channel()
        self.assertFalse(self.pickings.release_channel_id)

    @mute_logger("odoo.addons.stock_release_channel.models.stock_release_channel")
    def test_assign_outside_delivery_zone(self):
        """
        test assigning to release channel a geo-localized partner outside delivery zone
        """
        self.delivery_address_1.geo_point = self.outside_point
        self.delivery_address_2.geo_point = self.point2
        self.other_partner.geo_point = self.point3
        self.assertFalse(
            self.channel.delivery_zone.covers(self.delivery_address_1.geo_point)
        )
        self.pickings.assign_release_channel()
        self.assertFalse(self.picking.release_channel_id)
        self.assertEqual(self.picking2.release_channel_id, self.channel)
        self.assertEqual(self.picking3.release_channel_id, self.channel)

    @mute_logger("odoo.addons.stock_release_channel.models.stock_release_channel")
    def test_assign_not_geo_channel(self):
        """
        test default behavior for release channel without delivery zone
        """
        self.pickings.assign_release_channel()
        self.assertFalse(self.pickings.release_channel_id)
        self.channel.restrict_to_delivery_zone = False
        self.pickings.assign_release_channel()
        self.assertEqual(self.picking.release_channel_id, self.channel)
        self.assertEqual(self.picking2.release_channel_id, self.channel)
        self.assertEqual(self.picking3.release_channel_id, self.channel)

    def test_partner_release_channel(self):
        """
        test release channel is correctly set based on partner location
        """
        self.assertFalse(self.other_partner.located_in_stock_release_channel_ids)
        self.other_partner.geo_point = self.point1
        self.assertEqual(
            self.other_partner.located_in_stock_release_channel_ids, self.channel
        )
        self.other_partner.geo_point = self.outside_point
        self.assertFalse(self.other_partner.located_in_stock_release_channel_ids)
        self.other_partner.geo_point = self.point1
        self.assertEqual(
            self.other_partner.located_in_stock_release_channel_ids, self.channel
        )
        self.other_partner.in_geo_release_channel = False
        self.assertFalse(self.other_partner.located_in_stock_release_channel_ids)
