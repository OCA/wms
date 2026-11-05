# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockMove(models.Model):

    _inherit = "stock.move"

    def _extract_in_split_order(self, default=None, backorder=False):
        """
        Copy the release channel in this case

        Can't pass release_channel_id to copy() for multi-company reasons
        (the company_id is computed after accessing some picking fields at copy()).
        """
        picking = self.picking_id
        picking.ensure_one()
        new_picking = super()._extract_in_split_order(
            default=default, backorder=backorder
        )
        if picking.release_channel_id:
            new_picking.release_channel_id = picking.release_channel_id
        return new_picking
