# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import models


class StockMove(models.Model):

    _inherit = "stock.move"

    def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
        self = self.with_context(storage_quant=reserved_quant)
        return super()._prepare_move_line_vals(
            quantity=quantity, reserved_quant=reserved_quant
        )
