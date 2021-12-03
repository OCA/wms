# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import api, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.depends("order_line.availability_status", "picking_policy")
    def _compute_display_expected_date_ok(self):
        return super()._compute_display_expected_date_ok()

    def _get_display_expected_date_ok(self):
        # display_expected_date_ok is True if:
        #   - date is set (defined in sale_stock_available_to_promise_release)
        #   - any line is on order, fully available or partially available
        res = super()._get_display_expected_date_ok()
        lines = self.order_line.filtered(
            lambda l: not l.is_delivery
            and not l.display_type
            and not l.product_id.type == "service"
        )
        return res and lines._any_line_available()
