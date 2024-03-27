# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.osv.expression import AND


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _get_release_channel_possible_candidate_domain(self):
        self.ensure_one()
        domain = [("state", "not in", ("delivering", "delivering_error", "delivered"))]
        return AND([super()._get_release_channel_possible_candidate_domain(), domain])
