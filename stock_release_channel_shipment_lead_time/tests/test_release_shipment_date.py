# Copyright 2023 Camptocamp
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields

from odoo.addons.stock_release_channel.tests.common import ChannelReleaseCase


class TestChannelReleaseShipmentLeadTime(ChannelReleaseCase):
    def test_shipment_date(self):
        self.channel.warehouse_id.calendar_id = False
        self.channel.process_end_time = 12
        self.channel.process_end_date = "2023-09-11"
        self.channel.shipment_lead_time = 4
        self.assertEqual(
            "2023-09-15",
            fields.Date.to_string(self.channel.shipment_date),
        )

    def test_shipment_date_with_calendar(self):
        self.channel.warehouse_id = self.wh
        self.channel.warehouse_id.calendar_id = self.env.ref(
            "resource.resource_calendar_std"
        )
        self.channel.process_end_time = 12
        self.channel.process_end_date = "2023-06-30"
        self.channel.shipment_lead_time = 6
        self.assertEqual(
            "2023-07-10",
            fields.Date.to_string(self.channel.shipment_date),
        )
