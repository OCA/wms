# Copyright 2025 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

from freezegun import freeze_time

from odoo import fields

from .common import StockReleaseChannelDeliveryDateCommon

to_datetime = fields.Datetime.to_datetime


class TestStockReleaseChannelDeliverydate(StockReleaseChannelDeliveryDateCommon):
    @freeze_time("2025-01-02 10:00:00")
    def test_delivery_date(self):
        """Test generator on channel object"""
        now = fields.Datetime.now()
        dt = self.channel._get_earliest_delivery_date(self.partner, now)
        self.assertEqual(dt, to_datetime("2025-01-04 10:00:00"))
