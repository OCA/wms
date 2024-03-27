# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    stock_release_channel_delivery_weekday_ids = fields.Many2many(
        "time.weekday",
        compute="_compute_stock_release_channel_delivery_weekday_ids",
        readonly=True,
        store=True,
    )

    @api.depends("stock_release_channel_ids.preparation_weekday_ids")
    def _compute_stock_release_channel_delivery_weekday_ids(self):
        for partner in self:
            partner.stock_release_channel_delivery_weekday_ids = (
                partner.stock_release_channel_ids.preparation_weekday_ids
            )
