# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class StockReleaseChannel(models.Model):
    _inherit = "stock.release.channel"

    shipment_planning_method = fields.Selection(
        selection=[("none", "None"), ("simple", "Simple")],
        required=True,
        default="none",
    )
    picking_to_plan_ids = fields.Many2many(
        comodel_name="stock.picking", compute="_compute_picking_to_plan_ids"
    )
    can_plan_shipment = fields.Boolean(compute="_compute_can_plan_shipment")
    shipment_advice_ids = fields.One2many(
        comodel_name="shipment.advice",
        inverse_name="release_channel_id",
        string="Shipment Advices",
        readonly=True,
    )

    def button_show_shipment_advice(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Shipment Advice"),
            "view_mode": "calendar,tree,form",
            "res_model": self.shipment_advice_ids._name,
            "domain": [("release_channel_id", "=", self.id)],
            "context": self.env.context,
        }

    @api.depends("shipment_planning_method", "picking_to_plan_ids")
    def _compute_can_plan_shipment(self):
        for rec in self:
            rec.can_plan_shipment = (
                rec.shipment_planning_method != "none" and rec.picking_to_plan_ids
            )

    @api.depends("picking_ids", "picking_ids.can_be_planned_in_shipment_advice")
    def _compute_picking_to_plan_ids(self):
        for rec in self:
            rec.picking_to_plan_ids = rec.picking_ids.filtered(
                "can_be_planned_in_shipment_advice"
            )

    def button_plan_shipments(self):
        self.ensure_one()
        if not self.can_plan_shipment:
            raise UserError(_("Shipment planning not allowed"))
        shipment_advices = self._plan_shipments()
        if not shipment_advices:
            return {}
        return {
            "type": "ir.actions.act_window",
            "name": _("Shipment Advice"),
            "view_mode": "tree,form",
            "res_model": shipment_advices._name,
            "domain": [("id", "in", shipment_advices.ids)],
            "context": self.env.context,
        }

    def _get_new_planner(self):
        planner = self.env["shipment.advice.planner"].new({})
        planner.shipment_planning_method = self.shipment_planning_method
        planner.release_channel_id = self
        return planner

    def _plan_shipments(self):
        shipment_advices = self.env["shipment.advice"]
        can_plan_channels = self.filtered("can_plan_shipment")
        for channel in can_plan_channels:
            planner = channel._get_new_planner()
            shipment_advices |= planner._plan_shipments_for_method()
        return shipment_advices
