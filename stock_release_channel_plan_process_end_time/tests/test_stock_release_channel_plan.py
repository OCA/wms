# Copyright 2023 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime

import pytz

from odoo import fields

from odoo.addons.partner_tz.tools.tz_utils import tz_to_utc_naive_datetime
from odoo.addons.stock_release_channel_plan.tests.common import ReleaseChannelPlanCase
from odoo.addons.stock_release_channel_process_end_time.utils import float_to_time


class TestStockReleaseChannelPlan(ReleaseChannelPlanCase):
    def test_launch_plan(self):
        channel = self.plan1_channel1
        channel.process_end_date = False
        tz_name = "Europe/Brussels"
        channel.warehouse_id.partner_id.tz = tz_name

        channel.write({"state": "asleep"})
        self._launch_channel(self.plan1)
        self.assertEqual(channel.state, "open")

        end_time = float_to_time(channel.process_end_time)  # in TZ
        end_date = datetime.combine(
            fields.Date.context_today(channel), end_time
        )  # in TZ
        end_date_utc = tz_to_utc_naive_datetime(channel.process_end_time_tz, end_date)
        self.assertEqual(
            channel.process_end_date,
            end_date_utc,
        )
        # Local Time is 10
        offset = pytz.timezone(tz_name).utcoffset(datetime.now()).total_seconds() / 3600
        self.assertEqual(
            channel.process_end_date.hour,
            10 - offset,
        )
        return
