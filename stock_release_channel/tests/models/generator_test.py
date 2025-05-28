# Copyright 2025 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

from datetime import timedelta

from odoo import models


class StockReleaseChannel(models.Model):
    _inherit = "stock.release.channel"

    @property
    def _delivery_date_generators(self):
        d = {}
        d["preparation"] = [
            self._next_delivery_date_one_day,
            self._next_delivery_date_two_days,
        ]
        return d

    def _next_delivery_date_one_day(self, delivery_date, partner=None):
        """Get the next valid delivery date respecting transport lead time.
        The delivery date must be postponed at least by the shipment lead time.
        """
        later = delivery_date + timedelta(days=1)
        while True:
            delivery_date = yield max(delivery_date, later)

    def _next_delivery_date_two_days(self, delivery_date, partner=None):
        """Get the next valid delivery date respecting transport lead time.
        The delivery date must be postponed at least by the shipment lead time.
        """
        later = delivery_date + timedelta(days=2)
        while True:
            delivery_date = yield max(delivery_date, later)
