# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    delivery_requires_other_lines = fields.Boolean(
        compute="_compute_delivery_requires_other_lines",
    )
    ignore_release_channel_block = fields.Boolean(default=False)
    blocked_for_channel_assignation = fields.Boolean(
        compute="_compute_blocked_for_channel_assignation",
        store=True,
        index=True,
    )
    blocked_for_channel_assignation_label = fields.Char(
        string="Channel Assignation Blocked",
        compute="_compute_blocked_for_channel_assignation_label",
    )

    @api.depends(
        "move_ids",
        "move_ids.delivery_requires_other_lines",
        "ignore_release_channel_block",
    )
    def _compute_blocked_for_channel_assignation(self):
        for picking in self:
            picking.blocked_for_channel_assignation = bool(
                picking.delivery_requires_other_lines
                and not picking.ignore_release_channel_block
            )

    @api.depends("move_ids", "move_ids.delivery_requires_other_lines")
    def _compute_delivery_requires_other_lines(self):
        for rec in self:
            rec.delivery_requires_other_lines = bool(rec.move_ids) and all(
                m.delivery_requires_other_lines for m in rec.move_ids
            )

    @api.depends("blocked_for_channel_assignation")
    def _compute_blocked_for_channel_assignation_label(self):
        for picking in self:
            if picking.blocked_for_channel_assignation:
                picking.blocked_for_channel_assignation_label = _("Blocked")
            else:
                picking.blocked_for_channel_assignation_label = ""

    def _create_backorder(self):
        backorders = super()._create_backorder()
        for move in backorders.move_ids:
            move.delivery_requires_other_lines = move._blocked_on_backorder()
        return backorders

    def button_ignore_release_channel_block(self):
        self.write({"ignore_release_channel_block": True})
        self.assign_release_channel()
        return True
