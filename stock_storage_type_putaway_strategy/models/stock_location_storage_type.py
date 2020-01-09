# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import api, fields, models


class StockLocationStorageType(models.Model):

    _inherit = "stock.location.storage.type"

    has_restrictions = fields.Boolean(compute="_compute_has_restrictions")

    @api.depends(
        "only_empty",
        "do_not_mix_lots",
        "do_not_mix_products",
        "max_height",
        "max_weight",
    )
    def _compute_has_restrictions(self):
        for slst in self:
            slst.has_restrictions = any(
                [
                    slst.only_empty,
                    slst.do_not_mix_lots,
                    slst.do_not_mix_products,
                    slst.max_height,
                    slst.max_weight,
                ]
            )
