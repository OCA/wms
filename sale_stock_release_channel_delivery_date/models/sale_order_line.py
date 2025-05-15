# Copyright 2025 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

from odoo import models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _expected_date(self):
        expected_dt = super()._expected_date()
        if self.product_id.type in ("product", "consu"):
            # we keep the added customer lead, it is the computation start dt
            channel_dt = self.order_id._get_release_channel_expected_date(expected_dt)
            if channel_dt:
                expected_dt = channel_dt
        return expected_dt
