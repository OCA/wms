# Copyright 2023 ACSONE SA/NV
# Copyright 2024 Camptocamp
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    is_release_blocked = fields.Boolean(
        string="Has Blocked Delivery",
        compute="_compute_is_release_blocked",
        search="_search_blocked_delivery",
    )
    release_blocked_label = fields.Char(
        string="Release Blocked",
        compute="_compute_release_blocked_label",
    )

    def _compute_is_release_blocked(self):
        for rec in self:
            rec.is_release_blocked = any(rec.move_ids.mapped("release_blocked"))

    def _search_blocked_delivery(self, operator, value):
        if operator not in ("=", "!="):
            raise ValueError(_("This operator is not supported"))
        return [("move_ids.release_blocked", operator, value)]

    @api.depends("is_release_blocked")
    def _compute_release_blocked_label(self):
        for rec in self:
            rec.release_blocked_label = _("Blocked") if rec.is_release_blocked else ""

    def _prepare_procurement_values(self, group_id=False):
        vals = super()._prepare_procurement_values(group_id=group_id)
        vals["release_blocked"] = self.order_id.block_release
        return vals
