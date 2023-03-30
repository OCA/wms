# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockReleaseChannel(models.Model):

    _inherit = "stock.release.channel"

    batch_mode = fields.Selection(
        selection_add=[("group_commercial_partner", "Grouped by Commercial Entiry")],
        ondelete={"group_commercial_partner": "set default"},
    )

    def _get_next_pickings_group_commercial_partner(self):
        # We have to use a python sort and not a order + limit on the search
        # because "date_priority" is computed and not stored. If needed, we
        # should evaluate making it a stored field in the module
        # "stock_available_to_promise_release".
        next_pickings = self._get_pickings_to_release().sorted(self._pickings_sort_key)
        if not next_pickings:
            return self.env["stock.picking"].browse()
        first_picking = next_pickings[0]
        commercial_partner = first_picking.commercial_partner_id
        partner_pickings = next_pickings.filtered(
            lambda p: p.commercial_partner_id == commercial_partner
        )
        return partner_pickings
