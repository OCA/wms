# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class ShipmentAdvicePlanner(models.TransientModel):

    _inherit = "shipment.advice.planner"

    def _prepare_toursolver_task_vals(self, warehouse, pickings_to_plan):
        vals = super()._prepare_toursolver_task_vals(warehouse, pickings_to_plan)
        vals.update(
            {
                "release_channel_id": self.release_channel_id.id,
                "name": self.release_channel_id.name,
            }
        )
        return vals
