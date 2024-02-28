# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockReleaseChannel(models.Model):

    _inherit = "stock.release.channel"

    shipment_planning_method = fields.Selection(
        selection_add=[("toursolver", "TourSolver")],
        ondelete={"toursolver": "cascade"},
    )
    delivery_resource_ids = fields.Many2many(
        comodel_name="toursolver.resource",
        string="Delivery resources",
        help="delivery resources to be considered in geo-optimazation",
    )

    def _get_new_planner(self):
        self.ensure_one()
        planner = super()._get_new_planner()
        planner.delivery_resource_ids = self.delivery_resource_ids
        return planner
