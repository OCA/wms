# Copyright 2020 Camptocamp (https://www.camptocamp.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    carrier_id = fields.Many2one(related="picking_id.carrier_id", store="True")
    sale_date_expected = fields.Date(
        "Delivery Date", related="group_id.date_expected", store="True"
    )
