# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class Company(models.Model):
    _inherit = "res.company"

    stock_reservation_horizon = fields.Integer(
        default=0,
        help="Compute promised quantities for order planned to be shipped "
        "until this number of days from today.",
    )
    stock_release_max_prep_time = fields.Integer(
        string="Transfer Releases Max Prep. Time",
        default=180.0,
        required=True,
        help="When your release transfers, their scheduled date is rescheduled "
        "to now + this preparation time (in minutes)."
        " Their scheduled date represents the latest the transfers should"
        " be done, and therefore, past this timestamp, considered late.",
    )
