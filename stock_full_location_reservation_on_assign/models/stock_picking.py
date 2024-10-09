# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def action_assign(self):
        res = super().action_assign()

        full_location_reservation_pickings = self.filtered(
            lambda p: p.picking_type_id.auto_full_location_reservation_on_assign
        )
        if full_location_reservation_pickings:
            full_location_reservation_pickings.do_full_location_reservation()
        return res
