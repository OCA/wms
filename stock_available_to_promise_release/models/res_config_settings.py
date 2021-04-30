# Copyright 2020 Camptocamp (https://www.camptocamp.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).


from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    stock_reservation_horizon = fields.Integer(
        related="company_id.stock_reservation_horizon", readonly=False,
    )
    stock_release_max_prep_time = fields.Integer(
        related="company_id.stock_release_max_prep_time", readonly=False,
    )
