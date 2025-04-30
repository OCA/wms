# Copyright 2025 Camptocamp SA, BCIM
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _refresh_warehouse_flow(self):
        flow_model = self.env["stock.warehouse.flow"]
        for move in self:
            if not move.need_release:
                continue
            flow_model._search_and_apply_for_move(move, assign_picking=True)
