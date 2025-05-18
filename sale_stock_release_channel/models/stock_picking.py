# Copyright 2025 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockPicking(models.Model):

    _inherit = "stock.picking"

    @property
    def _release_channel_possible_candidate_domain_apply_extras(self):
        """Do not apply extra domains when the delivery date is forced on the SO"""
        if self.sale_id.commitment_date:
            return False
        return super()._release_channel_possible_candidate_domain_apply_extras
