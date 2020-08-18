from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def split_other_move_lines(self, move_lines, intersection=False):
        """Substract `move_lines` from `move.move_line_ids`, put the result
        in a new move and returns it.

        If `intersection` is set to `True`, this is the common lines between
        `move_lines` and `move.move_line_ids` which will be put in a new move.
        """
        self.ensure_one()
        if intersection:
            other_move_lines = self.move_line_ids & move_lines
        else:
            other_move_lines = self.move_line_ids - move_lines
        if other_move_lines:
            qty_to_split = sum(other_move_lines.mapped("product_uom_qty"))
            backorder_move_id = self._split(qty_to_split)
            backorder_move = self.browse(backorder_move_id)
            backorder_move.move_line_ids = other_move_lines
            backorder_move._action_assign()
            return backorder_move
        return False
