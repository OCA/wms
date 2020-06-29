# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import api, models


class ChooseDeliveryCarrier(models.TransientModel):

    _inherit = "choose.delivery.carrier"

    @api.depends("partner_id", "order_id.shipping_weight")
    def _compute_available_carrier(self):
        super()._compute_available_carrier()
        for rec in self:
            carrier_preferences = self.env["sale.delivery.carrier.preference"].search(
                [
                    "&",
                    "|",
                    ("sale_order_max_weight", ">=", rec.order_id.shipping_weight,),
                    ("sale_order_max_weight", "=", 0.0,),
                    "|",
                    ("carrier_id", "in", rec.available_carrier_ids.ids),
                    ("carrier_id", "=", False),
                ]
            )
            carriers = carrier_preferences.mapped("carrier_id")
            if any([cp.preference == "partner" for cp in carrier_preferences]):
                carriers |= rec.order_id.partner_id.property_delivery_carrier_id
            rec.available_carrier_ids = carriers
