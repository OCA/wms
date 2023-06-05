# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ShipmentAdvicePlanner(models.TransientModel):

    _inherit = "shipment.advice.planner"

    release_channel_id = fields.Many2one(
        comodel_name="stock.release.channel", string="Release Channel"
    )
    picking_to_plan_ids = fields.Many2many(
        domain='[("can_be_planned_in_shipment_advice", "=", True),'
        '("release_channel_id", "=?", release_channel_id),]',
    )

    @api.model
    def _get_compute_picking_to_plan_ids_depends(self):
        return ["release_channel_id"]

    def _compute_picking_to_plan_ids(self):
        for rec in self:
            if rec.release_channel_id:
                rec.picking_to_plan_ids = rec.release_channel_id.picking_to_plan_ids
            else:
                super(ShipmentAdvicePlanner, rec)._compute_picking_to_plan_ids()
        return True

    def _prepare_shipment_advice_common_vals(self, picking_type):
        self.ensure_one()
        vals = super()._prepare_shipment_advice_common_vals(picking_type)
        if self.release_channel_id:
            vals["release_channel_id"] = self.release_channel_id.id
        return vals
