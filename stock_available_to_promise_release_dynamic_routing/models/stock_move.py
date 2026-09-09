# Copyright 2023 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

from itertools import groupby

from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _after_release_assign_moves(self):
        # Trigger the dynamic routing
        moves = super()._after_release_assign_moves()
        # Check if moves can be merged. We do this after the call to
        # _action_assign in super as this could delete some records in self
        sorted_moves_by_rule = sorted(moves, key=lambda m: m.picking_id.id)
        moves_to_rereserve_ids = []
        new_moves = self.browse()
        for _picking_id, move_list in groupby(
            sorted_moves_by_rule, key=lambda m: m.picking_id.id
        ):
            moves = self.browse(m.id for m in move_list)
            merged_moves = moves._merge_moves()
            new_moves |= merged_moves
            if moves != merged_moves:
                for move in merged_moves:
                    if not move.quantity_done:
                        moves_to_rereserve_ids.append(move.id)
        if moves_to_rereserve_ids:
            moves_to_rereserve = self.browse(moves_to_rereserve_ids)
            moves_to_rereserve._do_unreserve()
            moves_to_rereserve.with_context(
                exclude_apply_dynamic_routing=True
            )._action_assign()
        return new_moves
