# Copyright 2020 Camptocamp
# License OPL-1

from odoo import fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    release_channel_id = fields.Many2one(
        comodel_name="stock.release.channel", ondelete="restrict"
    )
