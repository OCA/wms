# Copyright 2025 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from datetime import timedelta

import pytz

from odoo import models


class StockReleaseChannel(models.Model):
    _inherit = "stock.release.channel"

    @property
    def _delivery_date_generators(self):
        d = super()._delivery_date_generators
        d["preparation"].append(self._next_delivery_date_warehouse_calendar)
        return d

    def _next_delivery_date_warehouse_calendar(self, delivery_date, partner=None):
        """Get the next valid delivery date respecting warehouse calendar

        The preparation date must be during warehouse working hours given by
        the calendar on the warehouse.

        A delivery date generator needs to provide the earliest valid date
        starting from the received date. It can be called multiple times with a
        new date to validate.
        """
        calendar = self.warehouse_id.calendar_id
        if not calendar:
            while True:
                delivery_date = yield delivery_date
        wh_tz = pytz.timezone(self.warehouse_id.partner_id.tz or "UTC")
        batch_delta = timedelta(days=61)
        while True:
            delivery_date = delivery_date.astimezone(pytz.utc)
            work_intervals = calendar._work_intervals_batch(
                delivery_date, delivery_date + batch_delta, tz=wh_tz
            )[False]
            for begin_dt_tz, end_dt_tz, _attendance in work_intervals:
                while delivery_date <= end_dt_tz:
                    if delivery_date < begin_dt_tz:
                        delivery_date = begin_dt_tz
                    delivery_date = yield delivery_date.astimezone(pytz.utc).replace(
                        tzinfo=None
                    )
                    delivery_date = delivery_date.astimezone(pytz.utc)
