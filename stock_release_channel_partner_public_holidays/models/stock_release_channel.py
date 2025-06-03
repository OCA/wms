# Copyright 2025 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import fields, models


class StockReleaseChannel(models.Model):

    _inherit = "stock.release.channel"

    exclude_public_holidays = fields.Boolean()

    @property
    def _delivery_date_generators(self):
        d = super()._delivery_date_generators
        d["customer"].append(self._next_delivery_date_partner_public_holiday)
        return d

    def _next_delivery_date_partner_public_holiday(self, delivery_date, partner):
        """Get the next valid delivery date respecting cutoff.

        The delivery date must not be a public holiday otherwise it is
        postponed to next open day.

        A delivery date generator needs to provide the earliest valid date
        starting from the received date. It can be called multiple times with a
        new date to validate.
        """
        self.ensure_one()
        partner.ensure_one()

        if not self.exclude_public_holidays:
            while True:
                delivery_date = yield delivery_date

        batch_delta = timedelta(days=61)
        delivery_date_tz = self._localize(delivery_date, tz=partner.tz)
        while True:
            end_dt_tz = delivery_date_tz + batch_delta
            all_holidays = self.env["hr.holidays.public"].get_holidays_list(
                start_dt=delivery_date_tz, end_dt=end_dt_tz, partner_id=partner.id
            )
            while delivery_date_tz <= end_dt_tz:
                if delivery_date_tz.date() not in all_holidays.mapped("date"):
                    delivery_date = yield self._naive(delivery_date_tz)
                    delivery_date_tz = self._localize(delivery_date, tz=partner.tz)
                else:
                    delivery_date_tz += timedelta(days=1)
                    delivery_date_tz = delivery_date_tz.replace(
                        hour=0, minute=0, second=0, microsecond=0
                    )
