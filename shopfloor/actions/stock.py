# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import _, fields
from odoo.tools.float_utils import float_round

from odoo.addons.component.core import Component

from ..exceptions import ConcurentWorkOnTransfer


class StockAction(Component):
    """Provide methods to work with stock operations."""

    _name = "shopfloor.stock.action"
    _inherit = "shopfloor.process.action"
    _usage = "stock"

    def _create_return_move__get_max_qty(self, origin_move):
        """Returns the max returneable qty."""
        # The max returnable qty is the sent qty minus the already returned qties
        quantity = origin_move.reserved_qty
        for move in origin_move.move_dest_ids:
            if (
                move.origin_returned_move_id
                and move.origin_returned_move_id != origin_move
            ):
                continue
            if move.state in ("partially_available", "assigned"):
                quantity -= sum(move.move_line_ids.mapped("reserved_qty"))
            elif move.state in ("done"):
                quantity -= move.reserved_qty
        return float_round(
            quantity, precision_rounding=origin_move.product_id.uom_id.rounding
        )

    def _create_return_move__get_vals(self, return_picking, origin_move):
        product = origin_move.product_id
        return_type = return_picking.picking_type_id
        return {
            "product_id": product.id,
            "product_uom": product.uom_id.id,
            "picking_id": return_picking.id,
            "state": "draft",
            "date": fields.Datetime.now(),
            "location_id": return_picking.location_id.id,
            "location_dest_id": return_picking.location_dest_id.id,
            "picking_type_id": return_type.id,
            "warehouse_id": return_type.warehouse_id.id,
            "origin_returned_move_id": origin_move.id,
            "procure_method": "make_to_stock",
        }

    def _create_return_move__link_to_origin(self, return_move, origin_move):
        move_orig_to_link = origin_move.move_dest_ids.mapped("returned_move_ids")
        move_orig_to_link |= origin_move
        origin_move_dest = origin_move.move_dest_ids.filtered(
            lambda m: m.state not in ("cancel")
        )
        move_orig_to_link |= origin_move_dest.move_orig_ids.filtered(
            lambda m: m.state not in ("cancel")
        )
        move_dest_to_link = origin_move.move_orig_ids.mapped("returned_move_ids")
        move_dest_orig = origin_move.returned_move_ids.move_orig_ids.filtered(
            lambda m: m.state not in ("cancel")
        )
        move_dest_to_link |= move_dest_orig.move_dest_ids.filtered(
            lambda m: m.state not in ("cancel")
        )
        write_vals = {
            "move_orig_ids": [(4, m.id) for m in move_orig_to_link],
            "move_dest_ids": [(4, m.id) for m in move_dest_to_link],
        }
        return_move.write(write_vals)

    def create_return_move(self, return_picking, origin_moves):
        """Creates a return move for a given return picking / move"""
        # Logic has been copied from
        # odoo_src/addons/stock/wizard/stock_picking_return.py
        for origin_move in origin_moves:
            # If max qty <= 0, it means that everything has been returned already.
            # Try with the next one from the recordset.
            max_qty = self._create_return_move__get_max_qty(origin_move)
            if max_qty > 0:
                return_move_vals = self._create_return_move__get_vals(
                    return_picking, origin_move
                )
                return_move_vals.update(product_uom_qty=max_qty)
                return_move = origin_move.copy(return_move_vals)
                self._create_return_move__link_to_origin(return_move, origin_move)
                return return_move

    def _create_return_picking__get_vals(self, return_types, origin):
        return_type = fields.first(return_types)
        return {
            "move_lines": [],
            "picking_type_id": return_type.id,
            "state": "draft",
            "origin": origin,
            "location_id": return_type.default_location_src_id.id,
            "location_dest_id": return_type.default_location_dest_id.id,
            "is_shopfloor_created": True,
        }

    def create_return_picking(self, picking, return_types, origin):
        # Logic has been copied from
        # odoo_src/addons/stock/wizard/stock_picking_return.py
        return_values = self._create_return_picking__get_vals(return_types, origin)
        return picking.copy(return_values)

    def mark_move_line_as_picked(
        self, move_lines, quantity=None, package=None, user=None, check_user=False
    ):
        """Set the qty_done and extract lines in new order"""
        user = user or self.env.user
        if check_user:
            picking_users = move_lines.picking_id.user_id
            if not all(pick_user == user for pick_user in picking_users):
                raise ConcurentWorkOnTransfer(
                    _("Someone is already working on these transfers")
                )
        for line in move_lines:
            qty_done = quantity if quantity is not None else line.reserved_uom_qty
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

    def unmark_move_line_as_picked(self, move_lines):
        """Reverse the change from `mark_move_line_as_picked`."""
        move_lines.write(
            {
                "shopfloor_user_id": False,
                "qty_done": 0,
                "result_package_id": False,
            }
        )
        pickings = move_lines.picking_id
        for picking in pickings:
            lines_still_assigned = picking.move_line_ids.filtered(
                lambda l: l.shopfloor_user_id
            )
            if lines_still_assigned:
                # Because there is other lines in the picking still assigned
                # The picking has to be split
                unmark_lines = picking.move_line_ids & move_lines
                unmark_lines._extract_in_split_order(default={"user_id": False})
            else:
                pickings.write(
                    {
                        "user_id": False,
                        "printed": False,
                    }
                )

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
        backorders = self.env["stock.picking"]
        for picking in moves.picking_id:
            # the backorder strategy is checked in the 'button_validate' method
            # on odoo standard. Since we call the sub-method '_action_done' here,
            # we have to set the context key 'cancel_backorder' as it is done
            # in the 'button_validate' method according to the backorder strategy.
            not_to_backorder = picking.picking_type_id.create_backorder == "never"
            picking = picking.with_context(cancel_backorder=not_to_backorder)
            moves_todo = picking.move_ids & moves
            if self._check_backorder(picking, moves_todo):
                existing_backorders = picking.backorder_ids
                picking._action_done()
                new_backorders = picking.backorder_ids - existing_backorders
                if new_backorders:
                    new_backorders.write({"user_id": False})
                backorders |= new_backorders
            else:
                backorders |= moves_todo.extract_and_action_done()
        return backorders

    def _check_backorder(self, picking, moves):
        """Check if the `picking` has to be validated as usual to create a backorder.

        We want to create a normal backorder if:

            - the moves are equal to all available moves of the current picking
              but there are still unavailable moves to process
            - the moves are not linked to unprocessed ancestor moves
        """
        assigned_moves = picking.move_ids.filtered(lambda m: m.state == "assigned")
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
