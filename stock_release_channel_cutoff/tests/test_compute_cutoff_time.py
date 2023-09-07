# Copyright 2023 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from datetime import datetime

from freezegun import freeze_time

from odoo.tests.common import TransactionCase


class TestStockReleaseChannel(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.stock_release_channel_default = cls.env.ref(
            "stock_release_channel.stock_release_channel_default"
        )
        cls.env.user.tz = "UTC"  # Timezone UTC

    @freeze_time("2023-02-01 9:00:00")
    def test_compute_cutoff_warning(self):
        self.stock_release_channel_default.write(
            {
                "cutoff_time": 8.0,
                "process_end_date": datetime.strptime(
                    "2023-02-01 9:00:00", "%Y-%m-%d %H:%M:%S"
                ),
            }
        )
        # Ensure the cutoff_warning is correctly computed in the user's timezone
        self.assertTrue(self.stock_release_channel_default.cutoff_warning)

        # Write record with a cutoff time in UTC+1
        self.env.user.tz = "Europe/Brussels"
        self.stock_release_channel_default.write(
            {
                "cutoff_time": 9.5,
            }
        )
        # Ensure the cutoff_warning is correctly computed in the user's timezone
        # 9:30 - 1:00 (UTC+1) = 8:30
        self.assertTrue(self.stock_release_channel_default.cutoff_warning)

        # Test the case when cutoff_time is empty
        self.stock_release_channel_default.write(
            {
                "cutoff_time": False,
            }
        )

        self.assertFalse(self.stock_release_channel_default.cutoff_warning)

    @freeze_time("2023-02-01 9:00:00")
    def test_cutoff_warning_with_process_end_date(self):
        # Test the case when the process end date is greater than now
        self.stock_release_channel_default.write(
            {
                "cutoff_time": 12.0,
                "process_end_date": datetime.strptime(
                    "2023-02-02 10:00:00", "%Y-%m-%d %H:%M:%S"
                ),
            }
        )
        self.assertFalse(self.stock_release_channel_default.cutoff_warning)

        self.stock_release_channel_default.write(
            {
                "cutoff_time": 8.0,
            }
        )
        self.assertFalse(self.stock_release_channel_default.cutoff_warning)

        # Test the case when the process end date is less than now
        self.stock_release_channel_default.write(
            {
                "cutoff_time": 12.0,
                "process_end_date": datetime.strptime(
                    "2023-1-31 10:00:00", "%Y-%m-%d %H:%M:%S"
                ),
            }
        )
        self.assertTrue(self.stock_release_channel_default.cutoff_warning)

        self.stock_release_channel_default.write(
            {
                "cutoff_time": 8.0,
                "process_end_date": datetime.strptime(
                    "2023-1-31 10:00:00", "%Y-%m-%d %H:%M:%S"
                ),
            }
        )
        self.assertTrue(self.stock_release_channel_default.cutoff_warning)
