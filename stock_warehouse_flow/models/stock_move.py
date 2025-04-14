# Copyright 2022 Camptocamp SA
# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    default_picking_type_id = fields.Many2one(
        "stock.picking.type",
        help=(
            "Used as a backup to save picking type set by odoo, "
            "before a new flow is applied."
        ),
    )

    def _apply_flow_on_action_confirm(self):
        if self.rule_id.route_id.apply_flow_on != "on_confirm":
            return False
        return self.picking_type_id.code == "outgoing"

    def _action_confirm(self, merge=True, merge_into=False):
        # Apply the flow configuration on the move before it generates
        # its chained moves (if any)
        FLOW = self.env["stock.warehouse.flow"]
        move_ids_to_confirm = []
        for move in self:
            if not move._apply_flow_on_action_confirm():
                move_ids_to_confirm.append(move.id)
                continue
            # Do not assign a picking within the _apply_on_move method
            # because it gets called later from _action_confirm itself
            move_ids_to_confirm += FLOW._search_and_apply_for_move(
                move, assign_picking=False
            ).ids
        moves_to_confirm = self.browse(move_ids_to_confirm)
        return super(StockMove, moves_to_confirm)._action_confirm(
            merge=merge, merge_into=merge_into
        )
