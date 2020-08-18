from odoo import _, fields, models
from odoo.exceptions import UserError


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    # TODO use a serialized field
    shopfloor_unloaded = fields.Boolean(default=False)
    shopfloor_postponed = fields.Boolean(
        default=False,
        copy=False,
        help="Technical field. "
        "Indicates if a the move has been postponed in a barcode scenario.",
    )
    shopfloor_checkout_done = fields.Boolean(default=False)
    shopfloor_user_id = fields.Many2one(comodel_name="res.users", index=True)

    # we search lines based on their location in some workflows
    location_id = fields.Many2one(index=True)
    package_id = fields.Many2one(index=True)

    # allow domain on picking_id.xxx without too much perf penalty
    picking_id = fields.Many2one(auto_join=True)

    def _split_pickings_from_source_location(self):
        """Ensure that the related pickings will have the same source location.

        Some pickings related could have other unrelated move lines, as such we
        have to split them to contain only the move lines related to the expected
        source location.

        Example:

            Initial data:

                PICK1:
                    - move line with source location LOC1
                    - move line with source location LOC2
                PICK2:
                    - move line with source location LOC2
                    - move line with source location LOC3

            Then we process move lines related to LOC2 with this method, we get:

                PICK1:
                    - move line with source location LOC1
                PICK2:
                    - move line with source location LOC3
                PICK3:
                    - move line with source location LOC2
                    - move line with source location LOC2

        Return the new picking (in case a split has been made), or the current
        related pickings.
        """
        location_src_to_process = self.location_id
        if location_src_to_process and len(location_src_to_process) != 1:
            raise UserError(
                _("Move lines processed have to share the same source location.")
            )
        pickings = self.picking_id
        move_lines_to_process_ids = []
        for picking in pickings:
            location_src = picking.mapped("move_line_ids.location_id")
            if len(location_src) == 1:
                continue
            # Get the related move lines among the picking and split them
            move_lines_to_process_ids.extend(
                set(picking.move_line_ids.ids) & set(self.ids)
            )
        # Put all move lines related to the source location in a separate picking
        move_lines_to_process = self.browse(move_lines_to_process_ids)
        new_move_ids = []
        for move_line in move_lines_to_process:
            new_move = move_line.move_id.split_other_move_lines(
                move_line, intersection=True
            )
            new_move._recompute_state()
            new_move_ids.append(new_move.id)
        # If we have new moves, create the backorder picking
        # NOTE: code copy/pasted & adapted from OCA module 'stock_split_picking'
        new_moves = self.env["stock.move"].browse(new_move_ids)
        if new_moves:
            picking = pickings[0]
            new_picking = picking.copy(
                {
                    "name": "/",
                    "move_lines": [],
                    "move_line_ids": [],
                    "backorder_id": picking.id,
                }
            )
            pickings.message_post(
                body=_(
                    'The backorder <a href="#" '
                    'data-oe-model="stock.picking" '
                    'data-oe-id="%d">%s</a> has been created.'
                )
                % (new_picking.id, new_picking.name)
            )
            new_moves.write({"picking_id": new_picking.id})
            new_moves.mapped("move_line_ids").write({"picking_id": new_picking.id})
            new_moves.move_line_ids.package_level_id.write(
                {"picking_id": new_picking.id}
            )
            new_moves._action_assign()
            pickings = new_picking
        return pickings
