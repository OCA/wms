# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _any_line_available(self):
        for line in self:
            if line.availability_status in ("full", "partial", "on_order"):
                return True
        return False
