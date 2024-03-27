# Copyright 2023 ACSONE SA/NV
# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    block_release_allowed = fields.Boolean(
        string="Block release allowed?",
        help="Technical field: tell if the release of operation can be blocked.",
        compute="_compute_block_release_allowed",
    )
    release_blocked = fields.Boolean(
        compute="_compute_release_blocked",
        store=True,
    )
    release_blocked_label = fields.Char(
        string="Release Blocked",
        compute="_compute_release_blocked_label",
    )

    @api.depends(
        "move_ids.rule_id.available_to_promise_defer_pull",
        "release_blocked",
        "state",
    )
    def _compute_block_release_allowed(self):
        for rec in self:
            rules = rec.move_ids.rule_id
            release_enabled = any(rules.mapped("available_to_promise_defer_pull"))
            rec.block_release_allowed = (
                release_enabled
                and not rec.release_blocked
                and rec.state in ("confirmed", "waiting")
            )

    @api.depends("move_ids", "move_ids.release_blocked")
    def _compute_release_blocked(self):
        for rec in self:
            shipping_policy = rec._get_shipping_policy()
            if shipping_policy == "one":
                rec.release_blocked = any(rec.move_ids.mapped("release_blocked"))
            else:
                rec.release_blocked = all(rec.move_ids.mapped("release_blocked"))

    @api.depends("release_blocked")
    def _compute_release_blocked_label(self):
        for rec in self:
            rec.release_blocked_label = _("Blocked") if rec.release_blocked else ""

    def _get_release_ready_depends(self):
        depends = super()._get_release_ready_depends()
        depends.append("move_ids.release_blocked")
        return depends

    def _create_backorder(self):
        backorders = super()._create_backorder()
        # Auto-block backorders
        for move in backorders.move_ids:
            if move.rule_id.autoblock_release_on_backorder:
                move.release_blocked = move._blocked_on_backorder()
        return backorders

    def action_block_release(self):
        """Block the release of the operation."""
        for rec in self:
            if not rec.block_release_allowed:
                continue
            rec.move_ids.action_block_release()

    def action_unblock_release(self):
        """Unblock the release of the operation."""
        self.move_ids.action_unblock_release()
