# Copyright 2025 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockPicking(models.Model):

    _inherit = "stock.picking"

    @property
    def _release_channel_possible_candidate_domain_partner_delivery_window(self):
        """The delivery date must be on a partner open day"""
        return [
            "|",
            ("respect_partner_delivery_time_windows", "=", False),
            (
                "delivery_date_weekday",
                "in",
                list(self.partner_id.delivery_time_weekdays),
            ),
        ]

    @property
    def _release_channel_possible_candidate_domain_extras(self):
        domains = super()._release_channel_possible_candidate_domain_extras
        domains.append(
            self._release_channel_possible_candidate_domain_partner_delivery_window
        )
        return domains
