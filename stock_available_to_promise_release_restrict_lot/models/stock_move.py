# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.osv.expression import AND, OR


class StockMove(models.Model):

    _inherit = "stock.move"

    def _previous_promised_qty_sql_lateral_where(self, warehouse):
        sql, params = super()._previous_promised_qty_sql_lateral_where(warehouse)
        sql += "AND m.restrict_lot_id is null"
        return sql, params

    def _get_previous_restricted_lot_moves_domain(self):
        return AND(
            [
                [
                    ("restrict_lot_id", "=", self.restrict_lot_id.id),
                    ("state", "not in", ["done", "cancel"]),
                    ("id", "!=", self.id),
                ],
                OR(
                    [
                        [("priority", ">", self.priority)],
                        [
                            ("priority", "=", self.priority),
                            ("date_priority", "<", self.date_priority),
                        ],
                        [
                            ("priority", "=", self.priority),
                            ("date_priority", "=", self.date_priority),
                            ("id", "<", self.id),
                        ],
                    ]
                ),
            ]
        )

    def _get_previous_restricted_lot_moves(self):
        self.ensure_one()
        if not self.restrict_lot_id:
            return self.browse()
        return self.search(self._get_previous_restricted_lot_moves_domain())

    def _get_previous_promised_qties(self):
        restrict_lot_moves = self.filtered("restrict_lot_id")
        no_restrict_lot_moves = self - restrict_lot_moves
        res = super(StockMove, no_restrict_lot_moves)._get_previous_promised_qties()
        for move in restrict_lot_moves:
            previous_moves = move._get_previous_restricted_lot_moves()
            res[move.id] = (
                sum(previous_moves.mapped("product_uom_qty")) if previous_moves else 0
            )
        return res

    def _get_ordered_available_to_promise_by_warehouse(self, warehouse):
        restrict_lot_moves = self.filtered("restrict_lot_id")
        no_restrict_lot_moves = self - restrict_lot_moves
        res = super(
            StockMove, no_restrict_lot_moves
        )._get_ordered_available_to_promise_by_warehouse(warehouse)
        if not warehouse:
            for move in restrict_lot_moves:
                res[move] = {
                    "ordered_available_to_promise_uom_qty": 0,
                    "ordered_available_to_promise_qty": 0,
                }
            return res
        location_domain = warehouse.view_location_id._get_available_to_promise_domain()
        domain_quant = AND(
            [[("lot_id", "in", self.restrict_lot_id.ids)], location_domain]
        )
        location_quants = self.env["stock.quant"].read_group(
            domain_quant, ["lot_id", "quantity"], ["lot_id"], orderby="id"
        )
        quants_available = {
            item["lot_id"][0]: item["quantity"] for item in location_quants
        }
        for move in restrict_lot_moves:
            available_qty = quants_available.get(move.restrict_lot_id.id, 0.0)
            res[move] = move._get_ordered_available_to_promise_qty(available_qty)
        return res
