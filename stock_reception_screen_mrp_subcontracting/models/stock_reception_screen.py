# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import models


class StockReceptionScreen(models.Model):
    _inherit = "stock.reception.screen"

    def _split_move(self, move, qty):
        # Overridden to remove the link between the move of finished product
        # and the move to receive to not update the qty to produce on the MO
        # with a partial received qty. That way we always keep the original qty
        # to produce on the MO while having the received qty split among
        # several moves in the receipt.
        move_is_subcontract = move.is_subcontract
        move_move_orig = move.move_orig_ids
        if move_is_subcontract:
            move.move_orig_ids = False
        new_move = super()._split_move(move, qty)
        if move_is_subcontract:
            # Link the finished product move with the remaining move to process
            new_move.move_orig_ids = move_move_orig
            # Restore the link between the finished product move with the received one
            move.move_orig_ids = move_move_orig
        return new_move

    def _validate_current_move(self):
        # Overridden to automatically recheck availability each time a move
        # is validated to reserve qties from the production for remaining moves
        res = super()._validate_current_move()
        if self.current_move_id.is_subcontract:
            if self.picking_id.state not in ("cancel", "done"):
                self.picking_id.action_assign()
        return res
