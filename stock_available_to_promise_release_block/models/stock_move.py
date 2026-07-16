# Copyright 2023 ACSONE SA/NV
# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from contextlib import contextmanager

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
        for move in self:
            if move.need_release:
                move.release_blocked = True

    def action_unblock_release(self):
        """Unblock the release."""
        self.release_blocked = False

    def _action_done(self, cancel_backorder=False):
        with self._manage_auto_block_release_on_backorder():
            return super()._action_done(cancel_backorder=cancel_backorder)

    @contextmanager
    def _manage_auto_block_release_on_backorder(self):
        """Context manager ensuring backorder moves inherit the auto-block.

        This is a workaround for 16.0, where stock.move has no
        _create_backorder method to hook into. The release_blocked field
        used to be set in stock.picking._create_backorder, but depending on
        the installed addons that method may not run, so the backorder moves
        could end up not blocked (e.g. with stock_picking_group_by_partner_by_carrier
        installed). This method should not be ported to later Odoo versions.

        Odoo's backorder split copies the current field values onto the new
        move, so the only way to make a backorder move blocked is to set
        release_blocked=True on the original move *before* calling super().
        We only ever apply the not-blocked -> blocked transition here; a
        move that is already blocked is left untouched, and we never
        auto-unblock.

        Steps:
        1. Before yielding (i.e. before the backorder split happens), collect
           the not-yet-done, partially delivered moves whose rule requires
           auto-blocking and that are not already blocked, and set
           release_blocked=True on all of them in one batched write.
        2. After the split, a move that ended up done/cancelled while still
           attached to its original picking was not actually split off into
           a backorder, so its forced value is reverted to False. Moves that
           were genuinely split (or are still ongoing) keep release_blocked
           = True; they are just marked modified so the field is
           recomputed/invalidated where needed.
        """
        to_block_ids = []
        picking_by_move = {}
        for move in self:
            if (
                move.state not in ("done", "cancel")
                and move.quantity_done < move.product_uom_qty
                and move.rule_id.autoblock_release_on_backorder
                and not move.release_blocked
                and move._blocked_on_backorder()
            ):
                to_block_ids.append(move.id)
                picking_by_move[move.id] = move.picking_id.id
        to_block = self.browse(to_block_ids)
        if to_block:
            with self.env.protecting([self._fields["release_blocked"]], to_block):
                to_block.release_blocked = True
        try:
            yield
        finally:
            if to_block:
                moves = self.browse(picking_by_move.keys())
                reverted = moves.filtered(
                    lambda m: m.state in ("done", "cancel")
                    and m.picking_id.id == picking_by_move[m.id]
                )
                if reverted:
                    with self.env.protecting(
                        [self._fields["release_blocked"]], reverted
                    ):
                        reverted.release_blocked = False
                kept = moves - reverted
                if kept:
                    kept.modified(["release_blocked"])
