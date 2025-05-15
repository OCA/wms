# Copyright 2025 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import fields, models
from odoo.osv import expression


class StockPicking(models.Model):

    _inherit = "stock.picking"

    def _get_release_channel_possible_candidate_domain_partner_public_holidays(self):
        now = fields.Datetime.now()
        all_holidays = self.env["hr.holidays.public"].get_holidays_list(
            start_dt=now,
            end_dt=now + timedelta(365),
            partner_id=self.partner_id.id,
        )
        if not all_holidays:
            return []
        return [
            "|",
            ("exclude_public_holidays", "=", False),
            ("shipment_date", "not in", all_holidays.mapped("date")),
        ]

    def _get_release_channel_possible_candidate_domain_channel(self):
        domain = super()._get_release_channel_possible_candidate_domain_channel()
        return expression.AND(
            [
                domain,
                self._get_release_channel_possible_candidate_domain_partner_public_holidays(),
            ]
        )
