# Copyright 2024 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# Copyright 2024 Camptocamp (https://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)


from odoo import fields

from odoo.addons.stock_release_channel.tests.common import ReleaseChannelCase

to_datetime = fields.Datetime.to_datetime


class TestChannelDeliveryDate(ReleaseChannelCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Mon-Fri 8:00-12:00 13:00-17:00
        cls.calendar = cls.env.ref("resource.resource_calendar_std")
        cls.wh.partner_id.tz = "Europe/Brussels"
        cls.channel = cls._create_channel(
            name="partner channel",
            warehouse_id=cls.wh.id,
        )

    def test_warehouse_calendar_no_calendar(self):
        dt = to_datetime("2023-02-01 08:00:00")
        gen = self.channel._next_delivery_date_warehouse_calendar(dt)
        result = next(gen)
        self.assertEqual(result, dt)
        result = gen.send(dt)
        self.assertEqual(result, dt)

    def test_warehouse_calendar_time_before_opening(self):
        self.wh.calendar_id = self.calendar
        dt = to_datetime("2025-01-06 06:30:00")  # Monday 07:30
        gen = self.channel._next_delivery_date_warehouse_calendar(dt)
        result = next(gen)
        opening = to_datetime("2025-01-06 07:00:00")  # Monday 08:00
        self.assertEqual(result, opening)
        result = gen.send(dt)
        self.assertEqual(result, opening)

    def test_warehouse_calendar_time_during_opening(self):
        self.wh.calendar_id = self.calendar
        dt = to_datetime("2025-01-06 07:30:00")  # Monday 08:30
        gen = self.channel._next_delivery_date_warehouse_calendar(dt)
        result = next(gen)
        self.assertEqual(result, dt)
        dt = to_datetime("2025-01-06 15:30:00")  # Monday 16:30
        result = gen.send(dt)
        self.assertEqual(result, dt)

    def test_warehouse_calendar_time_after_opening(self):
        self.wh.calendar_id = self.calendar
        dt = to_datetime("2025-01-06 16:30:00")  # Monday 17:30
        gen = self.channel._next_delivery_date_warehouse_calendar(dt)
        result = next(gen)
        next_day = to_datetime("2025-01-07 07:00:00")  # Tuesday 08:00
        self.assertEqual(result, next_day)

    def test_warehouse_calendar_day_before_opening(self):
        self.wh.calendar_id = self.calendar
        dt = to_datetime("2025-01-05 14:30:00")  # Sunday 15:30
        gen = self.channel._next_delivery_date_warehouse_calendar(dt)
        result = next(gen)
        opening = to_datetime("2025-01-06 07:00:00")  # Monday 08:00
        self.assertEqual(result, opening)
        result = gen.send(dt)
        self.assertEqual(result, opening)
