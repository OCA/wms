# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import models


class StockReceptionScreen(models.Model):
    _inherit = "stock.reception.screen"

    def _split_move(self, move, qty):
        # Overridden to remove the link between the move of finished product
        # and the move to receive to ease the split
        move_is_subcontract = move.is_subcontract
        move_move_orig = move.move_orig_ids
        if move_is_subcontract:
            move.move_orig_ids = False
        new_move_id = super()._split_move(move, qty)
        if move_is_subcontract:
            new_move = move.browse(new_move_id)
            new_move.move_orig_ids = move_move_orig
            move.move_orig_ids = move_move_orig
        return new_move_id

    def _validate_current_move(self):
        # Overridden to automatically recheck availability each time a move
        # is validated to reserve qties from the production for remaining moves
        res = super()._validate_current_move()
        if self.current_move_id.is_subcontract:
            if self.picking_id.state not in ("cancel", "done"):
                self.picking_id.action_assign()
        return res

    def _action_done_move(self, move):
        if move.is_subcontract:
            move = move.with_context(cancel_backorder=False)
        res = super()._action_done_move(move)
        return res

    def _action_done_picking(self):
        # Overridden to unlink existing move lines of finished products
        # as it is done in 'picking.action_done' in module 'mrp_subcontracting',
        # but here we do this only one time and not each time we iterate on
        # received move (which removes each time the move line created by the
        # previous received move, as in the context of reception screen we
        # could have received the goods in several moves while having only one
        # finished product move)
        for move in self.picking_id.move_lines:
            if not move.is_subcontract:
                continue
            if move._has_tracked_subcontract_components():
                move.move_orig_ids.filtered(
                    lambda m: m.state not in ("done", "cancel")
                ).move_line_ids.unlink()
        self = self.with_context(subcontracting_skip_unlink=True)
        return super()._action_done_picking()
