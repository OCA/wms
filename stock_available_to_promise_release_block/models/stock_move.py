# Copyright 2023 ACSONE SA/NV
# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models
from odoo.tools import float_is_zero


class StockMove(models.Model):
    _inherit = "stock.move"

    release_blocked = fields.Boolean(readonly=True)

    def _get_release_ready_depends(self):
        depends = super()._get_release_ready_depends()
        depends.append("release_blocked")
        return depends

    def _is_release_ready(self):
        # Override to not release moves that are blocked
        if not self.release_blocked:
            return super()._is_release_ready()
        return False

    def _blocked_on_backorder(self):
        return float_is_zero(
            self.ordered_available_to_promise_qty,
            precision_rounding=self.product_uom.rounding,
        )

    def action_block_release(self):
        """Block the release."""
        self.release_blocked = True

    def action_unblock_release(self):
        """Unblock the release."""
        self.release_blocked = False
