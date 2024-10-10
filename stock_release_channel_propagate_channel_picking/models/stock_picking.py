# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockPicking(models.Model):

    _inherit = "stock.picking"

    def _assign_release_channel_to_backorder(self, backorders):
        backorders_to_update = backorders.filtered(
            lambda backorder: not backorder.release_channel_id
            and backorder.picking_type_id.code != "outgoing"
        )
        for backorder in backorders_to_update:
            backorder.write(
                {"release_channel_id": backorder.backorder_id.release_channel_id.id}
            )

    def _create_backorder(self):
        backorders = super()._create_backorder()
        self._assign_release_channel_to_backorder(backorders)
        return backorders
