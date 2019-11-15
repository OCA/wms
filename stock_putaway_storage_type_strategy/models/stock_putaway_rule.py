# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import fields, models


class StockPutawayRule(models.Model):
    _inherit = 'stock.putaway.rule'

    location_out_id = fields.Many2one(
        # override the domain to allow dest being equal to source
        domain="[('id', 'child_of', location_in_id), "
               "'|', "
               "('company_id', '=', False), "
               "('company_id', '=', company_id)]",
    )
