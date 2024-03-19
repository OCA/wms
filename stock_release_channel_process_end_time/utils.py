# Copyright 2023 ACSONE SA/NV
# Copyright 2024 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import math
from datetime import datetime, time

import pytz

from odoo import fields
from odoo.tools import float_round

from odoo.addons.partner_tz.tools.tz_utils import (
    tz_to_utc_naive_datetime,
    utc_to_tz_naive_datetime,
)


def float_to_time(hours) -> time:
    """This returns a tuple (hours, minutes) from a float representation of time"""
    if hours == 24.0:
        return time.max
    fractional, integral = math.modf(hours)
    time_result = time(
        int(integral), int(float_round(60 * fractional, precision_digits=0)), 0
    )
    return time_result


def time_to_datetime(hours: time, now=False, tz=False) -> datetime:
    """Returns UTC datetime with given hours in local time"""
    if not tz:
        tz = pytz.utc
    now = now or fields.Datetime.now()
    now_tz = utc_to_tz_naive_datetime(tz, now)
    dt_tz = now_tz.replace(
        hour=hours.hour,
        minute=hours.minute,
        second=0,
        microsecond=0,
    )
    dt = tz_to_utc_naive_datetime(tz, dt_tz)
    return dt
