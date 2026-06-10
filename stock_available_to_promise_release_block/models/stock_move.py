# Copyright 2023 ACSONE SA/NV
# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    release_blocked = fields.Boolean(readonly=True)
    release_blocked_label = fields.Char(
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
        self.ensure_one()
        mode = self.rule_id.autoblock_release_on_backorder

        if mode == "always":
            return True

        if mode == "never":
            return False

        if mode == "single_customer_outgoing_move":
            if self.picking_code != "outgoing":
                return False

            partner = self.partner_id
            if not partner:
                return False

            # Block if no other out moves for this client
            other_move_exists = bool(
                self.search_count(
                    [
                        ("id", "!=", self.id),
                        ("partner_id", "=", partner.id),
                        ("state", "in", ["confirmed", "waiting", "assigned"]),
                        ("picking_code", "=", "outgoing"),
                    ],
                    limit=1,
                )
            )
            return not other_move_exists

        return False

    def action_block_release(self):
        """Block the release."""
        for move in self:
            if move.need_release:
                move.release_blocked = True

    def action_unblock_release(self):
        """Unblock the release."""
        self.release_blocked = False
