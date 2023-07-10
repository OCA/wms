# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import _, api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    total_weight = fields.Float(
        compute="_compute_picking_info",
        help="Technical field. Indicates total weight of transfers included.",
    )
    move_line_count = fields.Integer(
        compute="_compute_picking_info",
        help="Technical field. Indicates number of move lines included.",
    )
    package_level_count = fields.Integer(
        compute="_compute_picking_info",
        help="Technical field. Indicates number of package_level included.",
    )
    bulk_line_count = fields.Integer(
        compute="_compute_picking_info",
        help="Technical field. Indicates number of move lines without package included.",
    )
    is_shopfloor_created = fields.Boolean()

    @api.depends(
        "move_line_ids", "move_line_ids.product_qty", "move_line_ids.product_id.weight"
    )
    def _compute_picking_info(self):
        for item in self:
            item.update(
                {
                    "total_weight": item._calc_weight(),
                    "move_line_count": len(item.move_line_ids),
                    "package_level_count": len(item.package_level_ids),
                    # NOTE: not based on 'move_line_ids_without_package' field
                    # on purpose as it also takes into account the
                    # 'Move entire packs' option from the picking type.
                    "bulk_line_count": len(
                        item.move_line_ids.filtered(lambda ml: not ml.package_level_id)
                    ),
                }
            )

    def _calc_weight(self):
        weight = 0.0
        for move_line in self.mapped("move_line_ids"):
            weight += move_line.product_qty * move_line.product_id.weight
        return weight

    def _check_move_lines_map_quant_package(self, package):
        # see tests/test_move_action_assign.py for details
        pack_move_lines = self.move_line_ids.filtered(
            lambda ml: ml.package_id == package
        )
        # if we set a qty_done on any line, it's picked, we don't want
        # to change it in any case, so we ignore the package level
        if any(pack_move_lines.mapped("qty_done")):
            return False
        # if we already changed the destination package, do not create
        # a new package level
        if any(
            line.result_package_id != package
            for line in pack_move_lines
            if line.result_package_id
        ):
            return False
        return super()._check_move_lines_map_quant_package(package)

    def split_assigned_move_lines(self, move_lines=None):
        """Put all reserved quantities (move lines) in their own moves and transfer.

        As a result, the current transfer will contain only confirmed moves.
        """
        self.ensure_one()
        # Check in the picking all the moves which are partially available or confirmed
        moves = self.move_lines.filtered(
            lambda m: m.state in ("partially_available", "confirmed")
        )
        # If one of these moves has an ancestor, split the moves
        # then extract all the assigned moves in a new transfer.
        # Indeed, a move without ancestor won't see its reserved qty changed
        # automatically over time.
        has_ancestors = bool(
            moves.move_orig_ids.filtered(lambda m: m.state not in ("cancel", "done"))
        )
        if not has_ancestors:
            return self.id
        # Get only transfers composed of moves assigned or confirmed
        moves.split_other_move_lines(moves.move_line_ids)
        # Put assigned moves related to processed move lines into a separate transfer
        if move_lines:
            assigned_moves = self.move_lines & move_lines.move_id
        else:
            assigned_moves = self.move_lines.filtered(lambda m: m.state == "assigned")
        if assigned_moves == self.move_lines:
            return self.id
        new_picking = self.copy(
            {
                "name": "/",
                "move_lines": [],
                "move_line_ids": [],
                "backorder_id": self.id,
            }
        )
        message = _(
            'The backorder <a href="#" '
            'data-oe-model="stock.picking" '
            'data-oe-id="%d">%s</a> has been created.'
        ) % (new_picking.id, new_picking.name)
        self.message_post(body=message)
        assigned_moves.write({"picking_id": new_picking.id})
        assigned_moves.mapped("move_line_ids").write({"picking_id": new_picking.id})
        assigned_moves.move_line_ids.package_level_id.write(
            {"picking_id": new_picking.id}
        )
        assigned_moves._action_assign()
        return new_picking.id
