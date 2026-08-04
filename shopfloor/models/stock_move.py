# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# Copyright 2022 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import _, models
from odoo.tools.float_utils import float_compare, float_is_zero


class StockMove(models.Model):
    _inherit = "stock.move"

    @property
    def picked(self):
        """:return: True if there is a quantity picked."""
        self.ensure_one()
        return (
            float_compare(
                self.quantity_done,
                0,
                precision_rounding=self.product_uom.rounding,
            )
            > 0
        )

    @property
    def has_quantity_reserved(self):
        self.ensure_one()
        return not float_is_zero(
            self.reserved_availability, precision_rounding=self.product_uom.rounding
        )

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
                qty_to_split = sum(to_move.mapped("reserved_uom_qty"))
            else:
                qty_to_split = self.product_uom_qty - sum(
                    move_lines.mapped("reserved_uom_qty")
                )
            split_move_vals = self._split(qty_to_split)
            split_move = self.create(split_move_vals)
            split_move.move_line_ids = to_move
            split_move._action_confirm(merge=False)
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

    def _last_move_from_package_level(self):
        """Returns True if self is the last move in the related package level"""
        if self.package_level_id.move_ids - self:
            # More moves in package level than self
            return False
        move_lines = self.move_line_ids
        if move_lines.package_level_id.move_line_ids - move_lines:
            # More lines in package level than there's lines with package level
            return False
        return True

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
            "move_ids": [],
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
        self.move_line_ids.picking_id = new_picking.id
        # When package content is fully extracted to a new picking, also move
        # the package. Otherwise the package stays in current picking.
        if self._last_move_from_package_level():
            self.package_level_id.picking_id = new_picking.id
            self.move_line_ids.package_level_id.picking_id = new_picking.id
        else:
            self.package_level_id = False
            self.move_line_ids.package_level_id = False
            self.package_level_id.picking_id = False
            for line in self.move_line_ids:
                # We drop result package only if the whole package was
                # supposed to be moved.
                if line.package_id == line.result_package_id:
                    line.result_package_id = False

        # We skip the sanity check on the batch assignment to the new picking because in
        # some cases, the batch may contain done pickings, which would make the sanity check
        # fail. This could be the case when using the cluster_picking set_destination_all
        # method, when the batch contains lines partially processed from different pickings.
        new_picking.with_context(
            skip_batch_sanity_check=True
        ).batch_id = picking.batch_id
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
        new_backorders = self.env["stock.picking"]
        for picking in moves.picking_id:
            existing_backorders = picking.backorder_ids
            moves_todo = picking.move_ids & moves
            # No need to create a new transfer if we are processing all moves
            if moves_todo == picking.move_ids:
                new_picking = picking
            # We process some available moves of the picking, but there are still
            # some other moves to process, then we put the moves to process in
            # a new transfer to validate. All remaining moves stay in the
            # current transfer.
            else:
                new_picking = moves_todo._extract_in_split_order()
                assert new_picking.state == "assigned"
            new_picking._action_done()
            new_backorders |= new_picking.backorder_ids - existing_backorders
        return new_backorders
