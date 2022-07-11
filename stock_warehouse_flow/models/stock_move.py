# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _action_confirm(self, merge=True, merge_into=False):
        # Apply the flow configuration on the move before it generates
        # its chained moves (if any)
        for move in self:
            if not move._apply_flow_on_action_confirm():
                continue
            flow = self.env["stock.warehouse.flow"]._search_for_move(move)
            flow._apply_on_move(move)
        return super()._action_confirm(merge=merge, merge_into=merge_into)

    def _apply_flow_on_action_confirm(self):
        return self.picking_type_id.code == "outgoing"
