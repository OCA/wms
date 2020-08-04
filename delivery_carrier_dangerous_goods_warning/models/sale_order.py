# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import api, models


class SaleOrder(models.Model):

    _name = "sale.order"
    _inherit = ["sale.order", "dangerous.good.warning.mixin"]

    _line_field_name = "order_line"
    _line_doc_m2o_field_name = "order_id"

    @api.depends(
        "order_line", "order_line.product_id", "order_line.product_id.is_dangerous_good"
    )
    def _compute_contains_dangerous_goods(self):
        return super()._compute_contains_dangerous_goods()
