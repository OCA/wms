# Copyright 2020 Camptocamp
# License OPL-1

from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    release_channel_id = fields.Many2one(
        comodel_name="stock.release.channel", index=True, ondelete="restrict"
    )

    # TODO queue.job (with identity key)
    def assign_release_channel(self):
        self.env["stock.release.channel"].assign_release_channel(self)

    def _create_backorder(self):
        backorders = super()._create_backorder()
        self.env["stock.release.channel"].assign_release_channel(backorders)
        return backorders
