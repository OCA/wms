# Copyright 2022 Camptocamp SA
# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _apply_flow_on_release(self):
        if self.rule_id.route_id.apply_flow_on != "on_release":
            return False
        return self.picking_type_id.code == "outgoing"

    def _before_release(self):
        # Apply the flow when releasing the move
        res = super()._before_release()
        FLOW = self.env["stock.warehouse.flow"]
        move_ids_to_release = []
        for move in self:
            if not move._apply_flow_on_release():
                continue
            _move_ids_to_release = FLOW._search_and_apply_for_move(move).ids
            _move_ids_to_release.remove(move.id)
            move_ids_to_release += _move_ids_to_release
        if move_ids_to_release:
            self.browse(move_ids_to_release).release_available_to_promise()
        return res
