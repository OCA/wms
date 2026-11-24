# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _create_split_order(self, default=None):
        default = default or {}
        default = {**default, "release_channel_id": self.release_channel_id.id}
        return super()._create_split_order(default=default)
