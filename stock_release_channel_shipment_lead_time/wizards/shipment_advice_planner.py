# Copyright 2023 Camptocamp
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class ShipmentAdvicePlanner(models.TransientModel):
    _inherit = "shipment.advice.planner"

    def _prepare_shipment_advice_simple_vals_list(self, picking_type, pickings_to_plan):
        """
        override to set delivery_date in vals as shipment date of
        release channel
        - select max shipment date in the list of picking in case
            there are many pickings
        """
        self.ensure_one()
        res = super()._prepare_shipment_advice_simple_vals_list(
            picking_type, pickings_to_plan
        )
        for vals in res:
            shipment_dates = pickings_to_plan.mapped("release_channel_id").mapped(
                "shipment_date"
            )
            vals["delivery_date"] = shipment_dates and max(shipment_dates) or False
        return res
