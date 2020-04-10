# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class Company(models.Model):
    _inherit = "res.company"

    stock_reservation_horizon = fields.Integer(
        default=0,
        help="Compute promised quantities for order planned to be shipped "
        "until this number of days from today.",
    )
