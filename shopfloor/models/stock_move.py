# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# Copyright 2022 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import _, models
from odoo.tools.float_utils import float_compare


class StockMove(models.Model):
    _inherit = "stock.move"

    def _qty_is_satisfied(self):
        compare = float_compare(
            self.quantity_done,
            self.product_uom_qty,
            precision_rounding=self.product_uom.rounding,
        )
        # greater or equal
        return compare in (0, 1)

    def split_other_move_lines(self, move_lines, intersection=False):
        """Substract `move_lines` from `move.move_line_ids`, put the result
        in a new move and returns it.

        If `intersection` is set to `True`, this is the common lines between
        `move_lines` and `move.move_line_ids` which will be put in a new move.
        """
        self.ensure_one()
        other_move_lines = self.move_line_ids - move_lines
        if intersection:
            to_move = self.move_line_ids & move_lines
        else:
            to_move = other_move_lines
        if other_move_lines or self.state == "partially_available":
            if intersection:
                qty_to_split = sum(to_move.mapped("product_uom_qty"))
            else:
                qty_to_split = self.product_uom_qty - sum(
                    move_lines.mapped("product_uom_qty")
                )
            split_move_vals = self._split(qty_to_split)
            split_move = self.create(split_move_vals)
            split_move._action_confirm(merge=False)
            split_move.move_line_ids = to_move
            split_move._recompute_state()
            split_move._action_assign()
            self._recompute_state()
            return split_move
        return self.browse()

    def split_unavailable_qty(self):
        """Put unavailable qty of a partially available move in their own
        move (which will be 'confirmed').
        """
        partial_moves = self.filtered(lambda m: m.state == "partially_available")
        for partial_move in partial_moves:
            partial_move.split_other_move_lines(partial_move.move_line_ids)
        return partial_moves

    def _extract_in_split_order(self, default=None, backorder=False):
        """Extract moves in a new picking

        :param default: dictionary of field values to override in the original
            values of the copied record
        :param backorder: indicate if the original picking can be seen as a
            backorder after the split. You could apply a specific backorder
            strategy (e.g. cancel it).
        :return: the new order
        """
        picking = self.picking_id
        picking.ensure_one()
        data = {
            "name": "/",
            "move_lines": [],
            "move_line_ids": [],
            "backorder_id": picking.id,
        }
        data.update(dict(default or []))
        new_picking = picking.copy(data)
        link = '<a href="#" data-oe-model="stock.picking" data-oe-id="%d">%s</a>' % (
            new_picking.id,
            new_picking.name,
        )
        message = (_("The split order {} has been created.")).format(link)
        picking.message_post(body=message)
        self.picking_id = new_picking.id
        self.package_level_id.picking_id = new_picking.id
        self.move_line_ids.picking_id = new_picking.id
        self.move_line_ids.package_level_id.picking_id = new_picking.id
        self._action_assign()
        return new_picking

    def extract_and_action_done(self):
        """Extract the moves in a separate transfer and validate them.

        You can combine this method with `split_other_move_lines` method
        to first extract some move lines in a separate move, then validate it
        with this method.
        """
        # Process assigned moves
        moves = self.filtered(lambda m: m.state == "assigned")
        if not moves:
            return False
        for picking in moves.picking_id:
            moves_todo = picking.move_lines & moves
            # No need to create a new transfer if we are processing all moves
            if moves_todo == picking.move_lines:
                new_picking = picking
            # We process some available moves of the picking, but there are still
            # some other moves to process, then we put the moves to process in
            # a new transfer to validate. All remaining moves stay in the
            # current transfer.
            else:
                new_picking = moves_todo._extract_in_split_order()
                assert new_picking.state == "assigned"
            new_picking._action_done()
        return True
