# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import api, fields, models
from odoo.osv import expression


class StockWarehouseFlow(models.Model):
    _inherit = "stock.warehouse.flow"

    packaging_type_ids = fields.Many2many(
        "product.packaging.type", string="Packaging types"
    )
    split_method = fields.Selection(
        selection_add=[("packaging", "By Product Packaging")]
    )

    def _are_apply_conditions_equal(self, flow):
        res = super()._are_apply_conditions_equal(flow)
        if not res:
            return res

        if (
            self.packaging_type_ids & flow.packaging_type_ids
            or not self.packaging_type_ids
            and not flow.packaging_type_ids
        ):
            return True
        return False

    @api.constrains("packaging_type_ids")
    def _constrains_uniq(self):
        super()._constrains_uniq()

    def _is_split_allowed_for_packaging(self, packaging):
        self.ensure_one()
        packaging_type = packaging.packaging_type_id
        return packaging_type and packaging_type in self.packaging_type_ids

    def _split_move_by_packaging(self, move, packaging):
        self.ensure_one()
        move.ensure_one()
        packaging.ensure_one()
        split_qty = self._get_split_qty_multiple_of(move, packaging.qty)
        if split_qty:
            return self._split_move(move, split_qty)
        return move.browse([])

    def split_move_by_packaging(self, move):
        split_move_ids = []
        for packaging in move.product_id.packaging_ids:
            if not self._is_split_allowed_for_packaging(packaging):
                continue
            split_move = self._split_move_by_packaging(move, packaging)
            if split_move:
                split_move_ids.append(split_move.id)
                move = split_move
        return move.browse(split_move_ids)

    def split_move(self, move):
        split_moves = super().split_move(move)
        if self.split_method == "packaging":
            return self.split_move_by_packaging(move)
        return split_moves

    def _prepare_packaging_domain(self, move):
        return [
            "|",
            ("packaging_type_ids", "=", False),
            (
                "packaging_type_ids",
                "in",
                move.product_id.packaging_ids.packaging_type_id.ids,
            ),
        ]

    def _search_for_move_domain(self, move):
        domain = super()._search_for_move_domain(move)
        return expression.AND([domain, self._prepare_packaging_domain(move)])
