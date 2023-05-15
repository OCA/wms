# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval


class StockReleaseChannel(models.Model):

    _inherit = "stock.release.channel"

    carrier_id = fields.Many2one(
        comodel_name="delivery.carrier",
        help="The carrier linked to the release channel.",
        string="Transporter",
    )

    @api.onchange("carrier_id")
    def _onchange_carrier_id(self):
        if self.carrier_id:
            carrier_term = ("carrier_id.id", "=", self.carrier_id.id)
            safe_dom = safe_eval(self.rule_domain)
            if carrier_term not in safe_dom:
                # add the term in front of the domain if not present (=> AND)
                safe_dom.insert(0, carrier_term)
                self.rule_domain = str(safe_dom)
