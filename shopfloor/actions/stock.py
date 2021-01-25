# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.addons.component.core import Component


class StockAction(Component):
    """Provide methods to work with stock operations."""

    _name = "shopfloor.stock.action"
    _inherit = "shopfloor.process.action"
    _usage = "stock"

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
                picking.action_done()
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
