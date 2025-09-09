# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date, datetime

import pytz

from ..services.reception import UNSET
from .common import CommonCase


class TestDatetimeParsing(CommonCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # set the timezone of the warehouse to Brussels
        cls.wh.sudo().partner_id.tz = "Europe/Brussels"

    def test_to_iso_datetime_at_utc(self):
        user_tz = pytz.timezone("Europe/Brussels")

        # None and unset are passed through
        self.assertIsNone(self.service._to_iso_datetime_at_utc(None))
        self.assertIs(self.service._to_iso_datetime_at_utc(UNSET), UNSET)

        # Aware datetime in UTC is not changed
        dt_utc = pytz.utc.localize(datetime(2024, 6, 10, 12, 30))
        self.assertEqual(
            self.service._to_iso_datetime_at_utc(dt_utc),
            dt_utc.replace(tzinfo=None),
        )

        # Aware datetime in another timezone is converted to UTC
        dt_brussels = user_tz.localize(datetime(2024, 6, 10, 14, 30))
        self.assertEqual(
            self.service._to_iso_datetime_at_utc(dt_brussels),
            dt_utc.replace(tzinfo=None),
        )

        # Naive datetime is considered to be in user's timezone and converted to UTC
        dt_naive = datetime(2024, 6, 10, 14, 30)
        self.assertEqual(
            self.service._to_iso_datetime_at_utc(dt_naive),
            datetime(2024, 6, 10, 12, 30),
        )

        # Date is considered to be at midnight in user's timezone and converted to UTC
        d = date(2024, 6, 10)
        expected_dt = user_tz.localize(datetime(2024, 6, 10, 0, 0)).astimezone(pytz.UTC)
        self.assertEqual(
            self.service._to_iso_datetime_at_utc(d),
            expected_dt.replace(tzinfo=None),
        )

    def test_iso_datetime_str_parsing(self):

        # Date string is considered to be at midnight in user's timezone and converted to UTC
        d_str = "2024-06-10"
        self.assertEqual(
            self.service._to_iso_datetime_at_utc(d_str), datetime(2024, 6, 9, 22, 0)
        )

        # Datetime string without timezone is considered to be in user's timezone and
        # converted to UTC
        dt_str = "2024-06-10 14:30:00"
        self.assertEqual(
            self.service._to_iso_datetime_at_utc(dt_str), datetime(2024, 6, 10, 12, 30)
        )

        # Datetime string with timezone is converted to UTC
        dt_str_tz = "2024-06-10 14:30:00+02:00"
        self.assertEqual(
            self.service._to_iso_datetime_at_utc(dt_str_tz),
            datetime(2024, 6, 10, 12, 30),
        )
