# Copyright 2024 Foodles (https://www.foodles.co)
# @author Pierre Verkest <pierreverkest84@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    service_level_id = fields.Many2one(
        index="btree_not_null",
        comodel_name="stock.service.level",
        string="Service level",
    )

    def _prepare_procurement_values(self):
        return {
            **super()._prepare_procurement_values(),
            "service_level_id": self.service_level_id.id,
        }

    @api.model
    def _prepare_merge_moves_distinct_fields(self):
        return [
            *super()._prepare_merge_moves_distinct_fields(),
            "service_level_id",
        ]
