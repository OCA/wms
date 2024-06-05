# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class StockReleaseChannel(models.Model):

    _inherit = "stock.release.channel"

    def assign_release_channel(self, picking):
        """
        This will assign a release channel to existing origin
        pickings that are not done (e.g.: a backorder with no sleep/wakeup).
        """
        res = super().assign_release_channel(picking)
        if picking.release_channel_id:
            picking.move_ids._propagate_release_channel()

        return res
