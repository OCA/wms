# Copyright 2024 Camptocamp SA
# Copyright 2024 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import api, fields, models


class StockReleaseChannelPartnerDate(models.Model):
    _name = "stock.release.channel.partner.date"
    _description = "Release Channel for a specific delivery address and date"
    _order = "date DESC"

    active = fields.Boolean(default=True)
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        ondelete="cascade",
        string="Delivery Address",
        required=True,
        readonly=True,
        index=True,
    )
    release_channel_id = fields.Many2one(
        comodel_name="stock.release.channel",
        ondelete="cascade",
        string="Release Channel",
        required=True,
        index=True,
    )
    date = fields.Date(index=True)

    _sql_constraints = [
        (
            "uniq",
            "UNIQUE (partner_id, release_channel_id, date)",
            "A release channel for this date is already set.",
        ),
    ]

    @api.autovacuum
    def _gc_release_channel_partner_date(self):
        pref_rcs = self.with_context(active_test=False).search(
            self._gc_release_channel_partner_date_domain()
        )
        pref_rcs.unlink()

    def _gc_release_channel_partner_date_domain(self):
        return [("date", "<", fields.Date.subtract(fields.Date.today(), months=3))]
