# Copyright 2025 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

from datetime import timedelta

from odoo import models


class StockReleaseChannel(models.Model):
    _inherit = (  # pylint: disable=consider-merging-classes-inherited
        "stock.release.channel"
    )

    @property
    def _delivery_date_generators(self):
        d = {}
        d["preparation"] = [
            self._next_delivery_date_one_day,
            self._next_delivery_date_one_year,
        ]
        return d

    def _next_delivery_date_one_day(self, delivery_date, partner=None):
        """Get a next valid delivery date after 1 day"""
        later = delivery_date + timedelta(days=1)
        while True:
            delivery_date = yield max(delivery_date, later)

    def _next_delivery_date_one_year(self, delivery_date, partner=None):
        """Get a next valid delivery outside the limit"""
        later = delivery_date + timedelta(days=365)
        while True:
            delivery_date = yield max(delivery_date, later)
