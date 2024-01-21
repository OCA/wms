# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockReleaseChannelDeliverCheckWizard(models.TransientModel):

    _name = "stock.release.channel.deliver.check.wizard"
    _description = "stock release channel deliver check wizard"

    release_channel_id = fields.Many2one("stock.release.channel")

    def action_deliver(self):
        self.ensure_one()
        self.release_channel_id.unrelease_picking()
        return self.release_channel_id.action_deliver()
