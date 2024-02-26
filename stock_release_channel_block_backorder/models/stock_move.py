# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models
from odoo.tools import float_is_zero


class StockMove(models.Model):
    _inherit = "stock.move"

    delivery_requires_other_lines = fields.Boolean(readonly=True)

    def _blocked_on_backorder(self):
        return float_is_zero(
            self.ordered_available_to_promise_qty,
            precision_rounding=self.product_uom.rounding,
        )
