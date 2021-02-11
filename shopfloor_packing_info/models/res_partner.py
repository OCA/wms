# Copyright 2021 Camptocamp SA (https://www.camptocamp.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    shopfloor_packing_info_id = fields.Many2one(
        "shopfloor.packing.info",
        ondelete="restrict",
        string="Checkout Packing Information",
    )
