# Copyright 2022 Camptocamp SA
# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
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
        FLOW = self.env["stock.warehouse.flow"]
        move_ids_to_release = []
        for move in self:
            _move_ids_to_release = FLOW._search_and_apply_for_move(move).ids
            _move_ids_to_release.remove(move.id)
            move_ids_to_release += _move_ids_to_release
        if move_ids_to_release:
            self.browse(move_ids_to_release).release_available_to_promise()
