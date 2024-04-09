# Copyright 2023 ACSONE SA/NV
# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    release_blocked = fields.Boolean(readonly=True)
    release_blocked_label = fields.Char(
        string="Release Blocked",
        compute="_compute_release_blocked_label",
    )

    @api.depends("release_blocked")
    def _compute_release_blocked_label(self):
        for rec in self:
            rec.release_blocked_label = _("Blocked") if rec.release_blocked else ""

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
        """Hook that aims to be overridden."""
        return True

    def action_block_release(self):
        """Block the release."""
        if self.need_release:
            self.release_blocked = True

    def action_unblock_release(self):
        """Unblock the release."""
        self.release_blocked = False
