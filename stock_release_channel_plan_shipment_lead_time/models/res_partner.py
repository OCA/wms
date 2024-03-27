# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

from odoo import api, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.depends("stock_release_channel_ids.preparation_weekday_ids")
    def _compute_stock_release_channel_delivery_weekday_ids(self):
        # OVERRIDE to use delivery_weekday_ids instead of preparation_weekday_ids
        for partner in self:
            partner.stock_release_channel_delivery_weekday_ids = (
                partner.stock_release_channel_ids.delivery_weekday_ids
            )
