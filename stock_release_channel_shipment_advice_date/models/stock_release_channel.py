# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import math
from datetime import date, datetime, time, timedelta

import pytz

from odoo import api, fields, models


def float_to_time(hours_minutes: float) -> (int, int):
    hour = math.floor(hours_minutes)
    minute = round((hours_minutes % 1) * 60)
    if minute == 60:
        minute = 0
        hour += 1
    return hour, minute


class StockReleaseChannel(models.Model):
    _inherit = "stock.release.channel"

    planned_arrival_time = fields.Float(
        string="Arrival time",
        help="The scheduled arrival time of the shipment at the dock for loading.",
    )
    planned_arrival_datetime = fields.Datetime(
        string="Arrival date time",
        compute="_compute_planned_arrival_datetime",
        help="The planned arrival date time of the shipment at the dock for loading.",
    )
    planned_departure_time = fields.Float(
        string="Departure time",
        help="The planned time for the shipment to depart from the dock once it has "
        "been loaded.",
    )
    planned_departure_datetime = fields.Datetime(
        string="Departure date time",
        compute="_compute_planned_departure_datetime",
        help="The planned date time for the shipment to depart from the dock once it "
        "has been loaded.",
    )

    def _get_planned_date_time(self, planned_time):
        datetime_now = datetime.now()
        user_tz = pytz.timezone(self.env.user.tz)
        utc_tz = pytz.timezone("UTC")
        hours, minutes = float_to_time(planned_time)
        planned_time = time(hours, minutes)
        planned_datetime = datetime.combine(date.today(), planned_time)
        planned_datetime = (
            user_tz.localize(planned_datetime).astimezone(utc_tz).replace(tzinfo=None)
        )
        if planned_datetime <= datetime_now:
            planned_datetime += timedelta(days=1)
        return planned_datetime

    @api.depends("planned_departure_time")
    def _compute_planned_departure_datetime(self):
        for rec in self:
            rec.planned_departure_datetime = rec._get_planned_date_time(
                rec.planned_departure_time
            )

    @api.depends("planned_arrival_time")
    def _compute_planned_arrival_datetime(self):
        for rec in self:
            rec.planned_arrival_datetime = rec._get_planned_date_time(
                rec.planned_arrival_time
            )
