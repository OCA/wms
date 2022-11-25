# Copyright 2022 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.osv.expression import AND, NEGATIVE_TERM_OPERATORS, OR


class StockReleaseChannel(models.Model):

    _inherit = "stock.release.channel"

    release_mode = fields.Selection(
        selection_add=[("auto", "Automatic")],
        ondelete={"auto": "set default"},
    )

    is_auto_release_allowed = fields.Boolean(
        compute="_compute_is_auto_release_allowed",
        search="_search_is_auto_release_allowed",
    )

    @api.depends("release_mode", "is_release_allowed")
    def _compute_is_auto_release_allowed(self):
        for channel in self:
            channel.is_auto_release_allowed = (
                channel.release_mode == "auto" and channel.is_release_allowed
            )

    @api.model
    def _get_is_auto_release_allowed_domain(self):
        return AND(
            [self._get_is_release_allowed_domain(), [("release_mode", "=", "auto")]]
        )

    @api.model
    def _get_is_auto_release_not_allowed_domain(self):
        return OR(
            [
                self._get_is_release_not_allowed_domain(),
                [("release_mode", "!=", "auto")],
            ]
        )

    @api.model
    def _search_is_auto_release_allowed(self, operator, value):
        if "in" in operator:
            raise ValueError(f"Invalid operator {operator}")
        negative_op = operator in NEGATIVE_TERM_OPERATORS
        is_auto_release_allowed = (value and not negative_op) or (
            not value and negative_op
        )
        domain = self._get_is_auto_release_allowed_domain()
        if not is_auto_release_allowed:
            domain = self._get_is_auto_release_not_allowed_domain()
        return domain

    def write(self, vals):
        res = super().write(vals)
        release_mode = vals.get("release_mode")
        if release_mode == "auto":
            self.invalidate_recordset(["is_auto_release_allowed"])
            self.auto_release_all()
        return res

    def action_unlock(self):
        res = super().action_unlock()
        if not self.env.context.get("no_auto_release"):
            self.auto_release_all()
        return res

    def auto_release_all(self):
        pickings = self.filtered("is_auto_release_allowed")._get_pickings_to_release()
        pickings._delay_auto_release_available_to_promise()
