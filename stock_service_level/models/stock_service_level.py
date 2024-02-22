# Copyright 2024 Foodles (http://www.foodles.co).
# @author Pierre Verkest <pierreverkest84@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockServiceLevel(models.Model):
    _name = "stock.service.level"
    _description = "Stock Service level"

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True, index=True)

    _sql_constraints = [
        (
            "book_format_code_uniq",
            "unique(code)",
            "Code must be unique.",
        )
    ]

    def name_get(self):
        names = []
        for rec in self:
            names.append((rec.id, f"[{rec.code}] {rec.name}"))
        return names
