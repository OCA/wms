# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _apply_flow_on_action_confirm(self):
        # Override to not apply the flow configuration on moves to release.
        # The flow will be applied on the release, not before.
        if self.rule_id.route_id.available_to_promise_defer_pull:
            return False
        return super()._apply_flow_on_action_confirm()

    def _before_release(self):
        # Apply the flow when releasing the move
        super()._before_release()
        for move in self:
            flow = self.env["stock.warehouse.flow"]._search_for_move(move)
            flow._apply_on_move(move)
