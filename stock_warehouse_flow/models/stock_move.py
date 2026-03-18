# Copyright 2022 Camptocamp SA
# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
# © 2026 FactorLibre - Adriana Saiz <adriana.saiz@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    default_picking_type_id = fields.Many2one(
        "stock.picking.type",
        help=(
            "Used as a backup to save picking type set by odoo, "
            "before a new flow is applied."
        ),
    )
    wh_total_products = fields.Float(
        compute="_compute_wh_total_products",
        help=(
            "Total product units for the same sale order and warehouse. "
            "Equivalent to sale.order.total_products but scoped to the "
            "warehouse assigned to this move, useful for flow domain "
            "evaluation in multi-warehouse (omnichannel) scenarios."
        ),
    )

    @api.depends(
        "sale_line_id.order_id",
        "warehouse_id",
        "picking_type_id.warehouse_id",
        "product_uom_qty",
    )
    def _compute_wh_total_products(self):
        """Sum product_uom_qty of outgoing sibling moves sharing same SO and warehouse.

        Groups all non-cancelled outgoing moves by (sale_order, warehouse) in a
        single query, then assigns each group's total. Moves without
        sale_line_id fall back to their own product_uom_qty.

        Only outgoing moves are counted to avoid inflating the total with
        incoming (return) moves from exchange claims.

        Uses picking_type_id.warehouse_id as fallback when warehouse_id
        is not set (common after flow application in multi-warehouse scenarios).
        """
        moves_with_sale = self.filtered("sale_line_id")
        for move in self - moves_with_sale:
            move.wh_total_products = move.product_uom_qty
        if not moves_with_sale:
            return
        order_ids = moves_with_sale.sale_line_id.order_id.ids
        all_siblings = self.search(
            [
                ("sale_line_id.order_id", "in", order_ids),
                ("state", "!=", "cancel"),
                ("picking_type_id.code", "=", "outgoing"),
            ]
        )
        totals = {}
        for sibling in all_siblings:
            wh = sibling.warehouse_id or sibling.picking_type_id.warehouse_id
            key = (sibling.sale_line_id.order_id.id, wh.id)
            totals[key] = totals.get(key, 0.0) + sibling.product_uom_qty
        for move in moves_with_sale:
            wh = move.warehouse_id or move.picking_type_id.warehouse_id
            key = (move.sale_line_id.order_id.id, wh.id)
            move.wh_total_products = totals.get(key, move.product_uom_qty)

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
