# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockPicking(models.Model):

    _inherit = "stock.picking"

    def _get_release_channel_possible_candidate_domain_partner(self):
        self.ensure_one()
        domain = super()._get_release_channel_possible_candidate_domain_partner()
        if self.partner_id.in_geo_release_channel:
            domain += [
                "|",
                ("restrict_to_delivery_zone", "=", False),
                ("delivery_zone", "geo_intersect", self.partner_id.geo_point),
            ]
        else:
            domain += [("restrict_to_delivery_zone", "=", False)]
        return domain
