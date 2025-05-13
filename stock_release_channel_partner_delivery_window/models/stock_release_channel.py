# Copyright 2025 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime

from odoo import api, fields, models


class StockReleaseChannel(models.Model):

    _inherit = "stock.release.channel"

    respect_partner_delivery_time_windows = fields.Boolean(
        string="Respect Partner Delivery time windows",
        default=False,
        help=(
            "If the delivery has moves linked to SO lines linked to SO that has"
            " a commitment_date, then we never respect the partner time window "
            "(it is not an exclusion selection criteria anymore)"
        ),
    )

    delivery_date_weekday = fields.Integer(
        compute="_compute_delivery_date_weekday",
        store=True,
    )

    # Migration note: shipment_date will be renamed to delivery_date
    @api.depends(
        "shipment_date",
    )
    def _compute_delivery_date_weekday(self):
        for channel in self:
            if channel.shipment_date:
                channel.delivery_date_weekday = channel.shipment_date.weekday()
            else:
                channel.delivery_date_weekday = -1

    @property
    def _delivery_date_generators(self):
        d = super()._delivery_date_generators
        d["customer"].append(self._next_delivery_date_partner_delivery_window)
        return d

    def _next_delivery_date_partner_delivery_window(self, delivery_date, partner):
        """Get the next valid delivery date respecting customer delivery window.

        The delivery date must be when the customer is open.
        From the initial delivery_date, if the customer is not open on that
        date and time, postpone to the start of the next open window.

        A delivery date generator needs to provide the earliest valid date
        starting from the received date. It can be called multiple times with a
        new date to validate.
        """
        self.ensure_one()
        partner.ensure_one()
        if not self.respect_partner_delivery_time_windows:
            while True:
                delivery_date = yield delivery_date

        if partner.delivery_time_preference == "anytime":
            # no constrain, any date is valid
            while True:
                delivery_date = yield delivery_date

        tz = partner.tz
        if partner.delivery_time_preference == "workdays":
            # postpone to Monday when date is on a week-end
            while True:
                delivery_date_tz = self._localize(delivery_date, tz=tz)
                # postpone on Monday if Sat or Sun
                if delivery_date_tz.weekday() < 5:  # Mon-Fri
                    delivery_date = yield delivery_date
                    continue
                days = 0
                if delivery_date_tz.weekday() == 5:  # Sat
                    days = 1
                elif delivery_date_tz.weekday() == 6:  # Sun
                    days = 2
                delivery_date_tz = fields.Datetime.add(delivery_date_tz, days=days)
                delivery_date = self._naive(delivery_date_tz, reset_time=days)
                delivery_date = yield delivery_date

        while True:
            # yield first delivery window
            delivery_date_tz = self._localize(delivery_date, tz=tz)
            weekday = delivery_date_tz.weekday()
            for inc in range(8):
                # Each weekday is tested to find a window.
                # On the first day, we need a window that ends after current
                # delivery time. Afterwards, we just need a window.
                windows = partner.delivery_time_window_ids.filtered(
                    lambda w: str(weekday + inc)
                    in w.time_window_weekday_ids.mapped("name")
                    and (inc or w.get_time_window_end_time() >= delivery_date_tz.time())
                )
                if windows:
                    w = windows[0]
                    break
            else:
                # There is no time window, we consider any date valid
                while True:
                    delivery_date = yield delivery_date
            # Postpone the delivery date to that found window
            delivery_date_tz = datetime.combine(
                (fields.Datetime.add(delivery_date_tz, days=inc)).date(),
                max(w.get_time_window_start_time(), delivery_date_tz.time())
                if not inc
                else w.get_time_window_start_time(),
                tzinfo=delivery_date_tz.tzinfo,
            )
            delivery_date = self._naive(delivery_date_tz)
            delivery_date = yield delivery_date
