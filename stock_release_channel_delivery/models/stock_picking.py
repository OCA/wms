# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockPicking(models.Model):

    _inherit = "stock.picking"

    def _get_release_channel_possible_candidate_domain_picking(self):
        domain = super()._get_release_channel_possible_candidate_domain_picking()
        if self.carrier_id:
            domain.extend(
                [
                    "|",
                    ("carrier_ids", "=", False),
                    ("carrier_ids", "in", self.carrier_id.ids),
                ]
            )
        else:
            domain.extend([("carrier_ids", "=", False)])
        return domain
