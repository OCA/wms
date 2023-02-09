# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import math
from datetime import datetime, time, timedelta

import pytz

from odoo.tools import float_round

from odoo.addons.partner_tz.tools.tz_utils import tz_to_utc_time


def float_to_time(hours, tz=False) -> time:
    """This returns a tuple (hours, minutes) from a float representation of time"""
    if not tz:
        tz = pytz.utc
    if hours == 24.0:
        return time.max
    fractional, integral = math.modf(hours)
    time_result = time(
        int(integral), int(float_round(60 * fractional, precision_digits=0)), 0
    )
    time_result = tz_to_utc_time(tz, time_result)
    return time_result


def next_datetime(current: datetime, hours: time, **kwargs) -> datetime:
    repl = current.replace(
        hour=hours.hour, minute=hours.minute, second=0, microsecond=0, **kwargs
    )
    if hours.tzinfo:
        repl += hours.utcoffset()
    while repl <= current:
        repl = repl + timedelta(days=1)
    return repl
