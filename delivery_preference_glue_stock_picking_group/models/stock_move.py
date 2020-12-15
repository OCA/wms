# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models


class StockMove(models.Model):

    _inherit = "stock.move"

    def release_available_to_promise(self):
        """After release reset to customer prefered carrier the backorder."""
        pickings = self.filtered(
            lambda r: r.picking_id.picking_type_code == "outgoing"
            and r._filter_recompute_preferred_carrier
        ).mapped("picking_id")
        sales = pickings.sale_ids
        res = super().release_available_to_promise()
        need_release_pickings = sales.picking_ids.filtered("need_release")
        for picking in need_release_pickings:
            picking.carrier_id = picking.sale_id.carrier_id
        return res
