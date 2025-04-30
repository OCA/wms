# Copyright 2025 Camptocamp SA, BCIM
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def write(self, values):
        picking_carrier_mapping = {p.id: p.carrier_id for p in self}
        res = super().write(values)
        pickings_to_update = self.filtered(
            lambda p: picking_carrier_mapping.get(p.id) != p.carrier_id
        )
        pickings_to_update.move_ids._refresh_warehouse_flow()
        return res
