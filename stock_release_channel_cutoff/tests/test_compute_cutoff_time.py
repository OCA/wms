# Copyright 2023 Camptocamp
# Copyright 2024 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from datetime import datetime

from freezegun import freeze_time

from odoo import fields
from odoo.tests.common import TransactionCase

to_datetime = fields.Datetime.to_datetime


class TestStockReleaseChannelCutoff(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.channel = cls.env.ref("stock_release_channel.stock_release_channel_default")
        cls.channel.write(
            {
                "process_end_date": datetime.strptime(
                    "2023-02-01 9:00:00", "%Y-%m-%d %H:%M:%S"
                ),
            }
        )

    @freeze_time("2023-02-01 9:00:00")
    def test_compute_cutoff_no_warning(self):
        # No cutoff
        self.assertFalse(self.channel.cutoff_warning)
        # Cutoff after now
        self.channel.cutoff_time = 10.0
        self.assertFalse(self.channel.cutoff_warning)

    @freeze_time("2023-02-01 9:00:00")
    def test_compute_cutoff_warning(self):
        self.channel.cutoff_time = 8.0
        self.assertTrue(self.channel.cutoff_warning)

    @freeze_time("2023-02-01 9:00:00")
    def test_compute_cutoff_no_warning_tz(self):
        self.env.company.partner_id.tz = "Europe/Brussels"
        # It is now in local time 2023-02-01 10:00:00
        self.channel.cutoff_time = 10.5
        self.assertFalse(self.channel.cutoff_warning)

    @freeze_time("2023-02-01 9:00:00")
    def test_compute_cutoff_warning_tz(self):
        self.env.company.partner_id.tz = "Europe/Brussels"
        # It is now in local time 2023-02-01 10:00:00
        self.channel.cutoff_time = 9.5
        self.assertTrue(self.channel.cutoff_warning)

    @freeze_time("2023-01-31 9:00:00")
    def test_cutoff_warning_with_process_end_date_tomorrow(self):
        # Test the case when the process end date is tomorrow
        self.channel.cutoff_time = 10.0
        self.assertFalse(self.channel.cutoff_warning)

        self.channel.cutoff_time = 8.0
        self.assertFalse(self.channel.cutoff_warning)

    @freeze_time("2023-02-02 9:00:00")
    def test_cutoff_warning_with_process_end_date_yesterday(self):
        # Test the case when the process end date is yesterday
        self.channel.cutoff_time = 10.0
        self.assertTrue(self.channel.cutoff_warning)

        self.channel.cutoff_time = 8.0
        self.assertTrue(self.channel.cutoff_warning)

    @freeze_time("2023-02-01 09:00:00")
    def test_delivery_date_no_cutoff(self):
        self.channel.state = "asleep"
        self.env.company.partner_id.tz = "Europe/Brussels"
        self.channel.cutoff_time = 0
        dt = to_datetime("2023-02-01 08:00:00")
        gen = self.channel._next_delivery_date_cutoff(dt)
        result = next(gen)
        self.assertEqual(result, dt)
        result = gen.send(result)
        self.assertEqual(result, dt)

    @freeze_time("2023-02-01 09:00:00")
    def test_delivery_date_cutoff(self):
        self.channel.state = "asleep"
        self.env.company.partner_id.tz = "Europe/Brussels"
        self.channel.cutoff_time = 9.5  # = 8.5 in UTC
        # before cutoff
        dt = to_datetime("2023-02-01 08:00:00")
        gen = self.channel._next_delivery_date_cutoff(dt)
        result = next(gen)
        self.assertEqual(result, dt)
        result = gen.send(result)
        self.assertEqual(result, dt)
        # after cutoff
        dt = to_datetime("2023-02-01 09:00:00")
        result = gen.send(dt)
        next_day = to_datetime("2023-02-01 23:00:00")
        self.assertEqual(result, next_day)
        result = gen.send(result)
        self.assertEqual(result, next_day)
        dt = to_datetime("2023-02-02 09:00:00")
        result = gen.send(dt)
        self.assertEqual(result, dt)
