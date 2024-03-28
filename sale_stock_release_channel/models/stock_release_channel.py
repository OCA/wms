# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import api, models


class StockReleaseChannel(models.Model):
    _inherit = "stock.release.channel"

    @api.model
    def assign_release_channel(self, picking):
        # Override to propagate the release channel from order to picking
        picking.ensure_one()
        if picking.picking_type_id.code != "outgoing" or picking.state in (
            "cancel",
            "done",
        ):
            return
        sale_channel = picking.sale_id.release_channel_id
        if sale_channel:
            picking.release_channel_id = sale_channel
            return ""
        return super().assign_release_channel(picking)
