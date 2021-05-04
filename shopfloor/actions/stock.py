# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.addons.component.core import Component


class StockAction(Component):
    """Provide methods to work with stock operations."""

    _name = "shopfloor.stock.action"
    _inherit = "shopfloor.process.action"
    _usage = "stock"

    def is_src_location_valid(self, process, location):
        """Check the source location is valid for given process.

        We ensure the source is valid regarding one of the picking types of the
        process.
        """
        return location.is_sublocation_of(process.picking_types.default_location_src_id)

    def is_dest_location_valid(self, moves, location):
        """Check the destination location is valid for given moves.

        We ensure the destination is either valid regarding the picking
        destination location or the move destination location. With the push
        rules in the module stock_dynamic_routing in OCA/wms, it is possible
        that the move destination is not anymore a child of the picking default
        destination (as it is the last pushed move that now respects this
        condition and not anymore this one that has a destination to an
        intermediate location)
        """
        return location.is_sublocation_of(
            moves.picking_id.location_dest_id, all
        ) or location.is_sublocation_of(moves.location_dest_id, all)

    def is_dest_location_to_confirm(self, location_dest_id, location):
        """Check the destination location requires confirmation

        The location is valid but not the expected one: ask for confirmation
        """
        return not location.is_sublocation_of(location_dest_id)

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
