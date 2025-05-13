# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from freezegun import freeze_time

from odoo import fields
from odoo.fields import Command

from odoo.addons.stock_release_channel.tests.common import ReleaseChannelCase

to_datetime = fields.Datetime.to_datetime


class TestReleaseChannelLeadTimeWeekday(ReleaseChannelCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env.ref("stock.warehouse0")
        cls.default_channel.warehouse_id = cls.warehouse
        # Calendar creation copied from hr_holidays_public
        cls.calendar = cls.env["resource.calendar"].create(
            {"name": "Calendar", "attendance_ids": []}
        )
        for day in range(5):  # From monday to friday
            cls.calendar.attendance_ids = [
                (
                    0,
                    0,
                    {
                        "name": "Attendance",
                        "dayofweek": str(day),
                        "hour_from": "08",
                        "hour_to": "12",
                    },
                ),
                (
                    0,
                    0,
                    {
                        "name": "Attendance",
                        "dayofweek": str(day),
                        "hour_from": "14",
                        "hour_to": "18",
                    },
                ),
            ]
        time_weekday_mapping = dict(cls.env["time.weekday"]._fields["name"].selection)
        for val, name in time_weekday_mapping.items():
            setattr(
                cls,
                name.lower(),
                cls.env["time.weekday"].search([("name", "=", val)], limit=1),
            )

    def test_preparation_weekday_with_calendar(self):
        self.warehouse.calendar_id = self.calendar
        # Loop over a complete week and use freeze time to ensure computation does not
        #  rely on today
        for weekday in range(1, 8):
            self.default_channel.write({"delivery_weekday_ids": [Command.clear()]})
            with freeze_time("2024-01-0%s" % weekday):
                self.assertFalse(self.default_channel.preparation_weekday_ids)
                self.default_channel.shipment_lead_time = 3
                self.default_channel.write(
                    {"delivery_weekday_ids": [Command.link(self.monday.id)]}
                )
                self.assertIn(
                    self.wednesday, self.default_channel.preparation_weekday_ids
                )
                self.default_channel.write(
                    {"delivery_weekday_ids": [Command.link(self.tuesday.id)]}
                )
                self.assertIn(
                    self.thursday, self.default_channel.preparation_weekday_ids
                )
                self.default_channel.write(
                    {"delivery_weekday_ids": [Command.link(self.wednesday.id)]}
                )
                self.assertIn(self.friday, self.default_channel.preparation_weekday_ids)
                self.default_channel.write(
                    {"delivery_weekday_ids": [Command.link(self.thursday.id)]}
                )
                self.assertIn(self.monday, self.default_channel.preparation_weekday_ids)

                self.default_channel.write({"delivery_weekday_ids": [Command.clear()]})
                self.default_channel.shipment_lead_time = 10

                self.default_channel.write(
                    {"delivery_weekday_ids": [Command.link(self.monday.id)]}
                )
                self.assertIn(self.monday, self.default_channel.preparation_weekday_ids)
                self.default_channel.write(
                    {"delivery_weekday_ids": [Command.link(self.tuesday.id)]}
                )
                self.assertIn(
                    self.tuesday, self.default_channel.preparation_weekday_ids
                )
                self.default_channel.write(
                    {"delivery_weekday_ids": [Command.link(self.wednesday.id)]}
                )
                self.assertIn(
                    self.wednesday, self.default_channel.preparation_weekday_ids
                )
                self.default_channel.write(
                    {"delivery_weekday_ids": [Command.link(self.thursday.id)]}
                )
                self.assertIn(
                    self.thursday, self.default_channel.preparation_weekday_ids
                )

    def test_preparation_weekday_without_calendar(self):
        self.assertFalse(self.warehouse.calendar_id)
        # Loop over a complete week and use freeze time to ensure computation does not
        #  rely on today
        for weekday in range(1, 8):
            self.default_channel.write({"delivery_weekday_ids": [Command.clear()]})
            with freeze_time("2024-01-0%s" % weekday):
                self.assertFalse(self.default_channel.preparation_weekday_ids)
                self.default_channel.shipment_lead_time = 3
                self.default_channel.write(
                    {"delivery_weekday_ids": [Command.link(self.monday.id)]}
                )
                self.assertIn(self.friday, self.default_channel.preparation_weekday_ids)
                self.default_channel.write(
                    {"delivery_weekday_ids": [Command.link(self.tuesday.id)]}
                )
                self.assertIn(
                    self.saturday, self.default_channel.preparation_weekday_ids
                )
                self.default_channel.write(
                    {"delivery_weekday_ids": [Command.link(self.wednesday.id)]}
                )
                self.assertIn(self.sunday, self.default_channel.preparation_weekday_ids)
                self.default_channel.write(
                    {"delivery_weekday_ids": [Command.link(self.thursday.id)]}
                )
                self.assertIn(self.monday, self.default_channel.preparation_weekday_ids)

                self.default_channel.write({"delivery_weekday_ids": [Command.clear()]})
                self.default_channel.shipment_lead_time = 10

                self.default_channel.write(
                    {"delivery_weekday_ids": [Command.link(self.monday.id)]}
                )
                self.assertIn(self.friday, self.default_channel.preparation_weekday_ids)
                self.default_channel.write(
                    {"delivery_weekday_ids": [Command.link(self.tuesday.id)]}
                )
                self.assertIn(
                    self.saturday, self.default_channel.preparation_weekday_ids
                )
                self.default_channel.write(
                    {"delivery_weekday_ids": [Command.link(self.wednesday.id)]}
                )
                self.assertIn(self.sunday, self.default_channel.preparation_weekday_ids)
                self.default_channel.write(
                    {"delivery_weekday_ids": [Command.link(self.thursday.id)]}
                )
                self.assertIn(self.monday, self.default_channel.preparation_weekday_ids)

    @freeze_time("2025-01-02")
    def test_delivery_date_plan_weekdays(self):
        self.default_channel.write({"delivery_weekday_ids": [Command.clear()]})
        self.default_channel.shipment_lead_time = 2
        self.default_channel.write(
            {"delivery_weekday_ids": [Command.link(self.wednesday.id)]}
        )
        dt = fields.Datetime.now()  # Thursday
        gen = self.default_channel._next_delivery_date_plan_weekdays(dt)
        # next preparation date is on next Monday (Wed -2d lead time)
        result = next(gen)
        next_mon = to_datetime("2025-01-06 00:00:00")
        self.assertEqual(result, next_mon)
        result = gen.send(next_mon)
        self.assertEqual(result, next_mon)
        # if we add 1 day, the next preparation date is 1 week later
        result = gen.send(fields.Datetime.add(next_mon, days=1))
        self.assertEqual(result, fields.Datetime.add(next_mon, weeks=1))
