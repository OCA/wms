# Copyright 2023 ACSONE SA/NV
# Copyright 2025 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.osv import expression


class StockPicking(models.Model):

    _inherit = "stock.picking"

    @property
    def _release_channel_possible_candidate_domain_base(self):
        domain = super()._release_channel_possible_candidate_domain_base
        if self.carrier_id:
            domain_carrier = [
                "|",
                ("carrier_ids", "=", False),
                ("carrier_ids", "in", self.carrier_id.ids),
            ]
        else:
            domain_carrier = [("carrier_ids", "=", False)]
        domain = expression.AND([domain, domain_carrier])
        return domain
