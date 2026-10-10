# Copyright 2026 ACSONE SA/NV <https://www.acsone.eu>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.addons.component.core import Component


class ShopfloorSingleProductTransfer(Component):
    _inherit = "shopfloor.single.product.transfer"

    def _try_select_move_line(self, move_line):
        to_recompute = None
        if move_line.putaway_deferred:
            to_recompute = move_line
        elif self.work.menu.ignore_no_putaway_available and self._actions_for(
            "stock"
        ).no_putaway_available(self.picking_types, move_line):
            to_recompute = move_line
        if to_recompute:
            to_recompute._recompute_putaways()
            move_line = to_recompute
        return super()._try_select_move_line(move_line)

    def _split_move(self, move_line):
        return super()._split_move(move_line.with_context(deferred_putaway_apply=True))
