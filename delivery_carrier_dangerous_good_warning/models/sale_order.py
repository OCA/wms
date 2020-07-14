# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import api, models


class SaleOrder(models.Model):

    _inherit = "sale.order"

    @api.onchange("carrier_id")
    def _onchange_carrier_id(self):
        return self._check_dangerous_good()

    def _check_dangerous_good(self, carrier=None):
        self.ensure_one()
        warnings = {}
        if carrier is None:
            carrier = self.carrier_id
        if carrier and carrier.dangerous_goods_warning:
            for line in self.order_line:
                if (
                    line.product_id.limited_amount_id
                    in carrier.dangerous_goods_limited_amount_ids
                ):
                    warnings[line] = line.product_id.limited_amount_id
                # Other "dangerous goods" M2m fields to be defined on carrier
                # can be checked here to use the same warning machinery
        if warnings:
            return carrier._prepare_dangerous_goods_warning(warnings, "order_line")
