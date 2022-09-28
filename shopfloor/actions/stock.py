# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.addons.component.core import Component


class StockAction(Component):
    """Provide methods to work with stock operations."""

    _name = "shopfloor.stock.action"
    _inherit = "shopfloor.process.action"
    _usage = "stock"

    def mark_move_line_as_picked(
        self, move_lines, quantity=None, package=None, user=None
    ):
        """Set the qty_done and extract lines in new order"""
        user = user or self.env.user
        for line in move_lines:
            qty_done = quantity if quantity is not None else line.product_uom_qty
            line.qty_done = qty_done
            line._split_partial_quantity()
            data = {
                "shopfloor_user_id": user.id,
            }
            if package:
                # destination package is set to the scanned one
                data["result_package_id"] = package.id
            line.write(data)
        # Extract the picked quantity in a split order and set current user
        move_lines._extract_in_split_order(
            {
                "user_id": user.id,
                "printed": True,
            }
        )
        move_lines.picking_id.filtered(lambda p: p.user_id != user).user_id = user.id

    def validate_moves(self, moves):
        """Validate moves in different ways depending on several criterias:

        - moves to process are all the moves of the related transfer:
            the current transfer is validated
        - moves to process are a subset of available moves in the picking:
            the moves are put in a new transfer which is validated, the current
            transfer still have the remaining moves
        - moves to process are exactly the assigned moves of the related transfer:
            the transfer is validated as usual, creating a backorder.
        """
        moves.split_unavailable_qty()
        for picking in moves.picking_id:
            moves_todo = picking.move_lines & moves
            if self._check_backorder(picking, moves_todo):
                picking._action_done()
            else:
                moves_todo.extract_and_action_done()

    def _check_backorder(self, picking, moves):
        """Check if the `picking` has to be validated as usual to create a backorder.

        We want to create a normal backorder if:

            - the moves are equal to all available moves of the current picking
              but there are still unavailable moves to process
            - the moves are not linked to unprocessed ancestor moves
        """
        assigned_moves = picking.move_lines.filtered(lambda m: m.state == "assigned")
        has_ancestors = bool(
            moves.move_orig_ids.filtered(lambda m: m.state not in ("cancel", "done"))
        )
        return moves == assigned_moves and not has_ancestors

    def put_package_level_in_move(self, package_level):
        """Ensure to put the package level in its own move.

        In standard the moves linked to a package level could also be linked to
        other unrelated move lines. This method ensures that the package level
        will be attached to a move with only the relevant lines.
        This is useful to process a single package, having its own move makes
        this process easy.
        """
        package_move_lines = package_level.move_line_ids
        package_moves = package_move_lines.move_id
        for package_move in package_moves:
            # Check if there is no other lines linked to the move others than
            # the lines related to the package itself. In such case we have to
            # split the move to process only the lines related to the package.
            package_move.split_other_move_lines(package_move_lines)

    def no_putaway_available(self, picking_types, move_lines):
        """Returns `True` if no putaway destination has been computed for one
        of the given move lines.
        """
        base_locations = picking_types.default_location_dest_id
        # when no putaway is found, the move line destination stays the
        # default's of the picking type
        return any(line.location_dest_id in base_locations for line in move_lines)
