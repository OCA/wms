# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import api, models


class StockPicking(models.Model):

    _name = "stock.picking"
    _inherit = ["stock.picking", "dangerous.good.warning.mixin"]

    _line_field_name = "move_lines"
    _line_doc_m2o_field_name = "picking_id"

    @api.depends(
        "move_lines",
        "move_lines.product_id",
        "move_lines.product_id.is_dangerous_good",
    )
    def _compute_contains_dangerous_goods(self):
        return super()._compute_contains_dangerous_goods()
