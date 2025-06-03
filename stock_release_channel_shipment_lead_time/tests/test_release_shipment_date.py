# Copyright 2023 Camptocamp
# Copyright 2025 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields

from odoo.addons.stock_release_channel.tests.common import ChannelReleaseCase

to_datetime = fields.Datetime.to_datetime


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

    def test_delivery_date_shipment_lead_time(self):
        self.channel.warehouse_id = self.wh
        self.channel.warehouse_id.calendar_id = self.env.ref(
            "resource.resource_calendar_std"
        )
        self.channel.warehouse_id.partner_id.tz = "Europe/Brussels"
        self.channel.shipment_lead_time = 1
        dt = to_datetime("2025-01-02 08:00:00")  # Thursday
        gen = self.channel._next_delivery_date_shipment_lead_time(dt)
        result = next(gen)
        next_day = to_datetime("2025-01-02 23:00:00")  # Friday
        self.assertEqual(result, next_day)
        result = gen.send(dt)
        self.assertEqual(result, next_day)
        # around week-end
        dt = to_datetime("2025-01-03 08:00:00")  # Friday
        gen = self.channel._next_delivery_date_shipment_lead_time(dt)
        result = next(gen)
        next_day = to_datetime("2025-01-05 23:00:00")  # Monday
        self.assertEqual(result, next_day)
        result = gen.send(dt)
        self.assertEqual(result, next_day)
