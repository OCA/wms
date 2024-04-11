# Copyright 2023 ACSONE SA/NV
# Copyright 2024 Camptocamp
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockRule(models.Model):
    _inherit = "stock.rule"

    def _get_custom_move_fields(self):
        res = super()._get_custom_move_fields()
        res += ["release_blocked"]
        return res
