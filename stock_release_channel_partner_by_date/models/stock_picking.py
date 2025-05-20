# Copyright 2024 Camptocamp SA
# Copyright 2024 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    @property
    def _release_channel_partner_date_domain(self):
        assert self.scheduled_date
        scheduled_date = max(self.scheduled_date, fields.Datetime.now())
        tz = (
            self.picking_type_id.warehouse_id.partner_id.tz
            or self.env.company.partner_id.tz
            or "UTC"
        )
        date = fields.Datetime.context_timestamp(
            self.with_context(tz=tz),
            scheduled_date,
        ).date()
        return [
            ("partner_id", "=", self.partner_id.id),
            ("date", "=", date),
        ]

    def _get_release_channel_partner_dates(self):
        """Return specific channel entries corresponding to the transfer."""
        return (
            self.env["stock.release.channel.partner.date"]
            .search(self._release_channel_partner_date_domain)
            .filtered(
                lambda o: o.release_channel_id.filtered_domain(
                    self._release_channel_possible_candidate_domain_base
                )
            )
        )

    @property
    def _release_channel_possible_candidate_domain(self):
        # Look for a specific release channel at first
        if self.scheduled_date:
            specific_rcs = self._get_release_channel_partner_dates()
            if specific_rcs:
                return [
                    ("state", "in", ("open", "locked")),
                    ("id", "in", specific_rcs.release_channel_id.ids),
                ]
        return super()._release_channel_possible_candidate_domain
