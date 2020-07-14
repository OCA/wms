# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import api, models


class StockPicking(models.Model):

    _inherit = "stock.picking"

    @api.onchange("carrier_id")
    def _onchange_carrier_id(self):
        self._check_dangerous_good()

    def _check_dangerous_good(self):
        """Display a warning if any move has a good defined as dangerous and
        if this same dangerosity is defined on the carrier"""
        warnings = {}
        if self.carrier_id and self.carrier_id.dangerous_goods_warning:
            for move in self.move_lines:
                if (
                    move.product_id.limited_amount_id
                    in self.carrier_id.dangerous_goods_limited_amount_ids
                ):
                    warnings[move] = move.product_id.limited_amount_id
                # Other "dangerous goods" M2m fields to be defined on carrier
                # can be checked here to use the same warning machinery
        if warnings:
            return self.carrier_id._prepare_dangerous_goods_warning(warnings, "move")
