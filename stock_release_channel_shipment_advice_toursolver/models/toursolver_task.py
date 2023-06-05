# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ToursolverTask(models.Model):

    _inherit = "toursolver.task"

    release_channel_id = fields.Many2one(
        comodel_name="stock.release.channel", string="Release Channel", readonly=True
    )

    def _toursolver_new_shipment_advice_planer(self, resource, pickings_to_plan):
        planner = super()._toursolver_new_shipment_advice_planer(
            resource, pickings_to_plan
        )
        planner.release_channel_id = self.release_channel_id
        planner.picking_to_plan_ids = pickings_to_plan
        return planner
