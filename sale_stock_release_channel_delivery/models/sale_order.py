# Copyright 2025 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.osv import expression


class SaleOrder(models.Model):

    _inherit = "sale.order"

    @property
    def _release_channel_carrier_id(self):
        """Return the SO carrier or planned carrier at confirm"""
        return self.carrier_id

    @property
    def _release_channel_possible_candidate_domain_base(self):
        # Mimick the domain extension defined on stock.picking in
        # stock_release_channel_delivery
        domain = super()._release_channel_possible_candidate_domain_base
        if self._release_channel_carrier_id:
            domain_carrier = [
                "|",
                ("carrier_ids", "=", False),
                ("carrier_ids", "in", self._release_channel_carrier_id.id),
            ]
        else:
            domain_carrier = [("carrier_ids", "=", False)]
        domain = expression.AND([domain, domain_carrier])
        return domain
