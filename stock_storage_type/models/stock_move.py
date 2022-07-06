# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import models


class StockMove(models.Model):

    _inherit = "stock.move"

    def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
        self = self.with_context(storage_quant=reserved_quant)
        return super()._prepare_move_line_vals(
            quantity=quantity, reserved_quant=reserved_quant
        )

    def _action_assign(self):
        # The computation done by the putaway strategy is acting on moves, not
        # on the package levels that could be linked to several products/moves,
        # so we have to trigger the computation on the package level as well
        # to get the expected putaway destination.
        res = super()._action_assign()
        package_level_ids = [
            move.package_level_id.id
            for move in self
            if move.state == "assigned" and len(move.package_level_id.move_ids) > 1
        ]
        package_levels = self.env["stock.package_level"].browse(package_level_ids)
        package_levels.recompute_pack_putaway()
        return res
