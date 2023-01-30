# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import math
from datetime import datetime, time, timedelta

from odoo.tools import float_round


def float_to_time(hours) -> time:
    """This returns a tuple (hours, minutes) from a float representation of time"""
    if hours == 24.0:
        return time.max
    fractional, integral = math.modf(hours)
    return time(int(integral), int(float_round(60 * fractional, precision_digits=0)), 0)


def next_datetime(current: datetime, hours: time, **kwargs) -> datetime:
    repl = current.replace(hour=hours.hour, minute=hours.minute, **kwargs)
    while repl <= current:
        repl = repl + timedelta(days=1)
    return repl
