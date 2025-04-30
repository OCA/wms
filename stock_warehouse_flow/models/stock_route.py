# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import api, fields, models


class StockRoute(models.Model):
    _inherit = "stock.route"

    flow_id = fields.Many2one(
        comodel_name="stock.warehouse.flow",
        ondelete="set null",
        string="Routing Flow",
    )
    applicable_flow_ids = fields.One2many(
        comodel_name="stock.warehouse.flow",
        compute="_compute_applicable_flow_ids",
        string="Applicable Flows",
    )
    apply_flow_on = fields.Selection(
        [("on_confirm", "When move is confirmed")], default="on_confirm"
    )

    @api.depends("rule_ids.picking_type_id")
    def _compute_applicable_flow_ids(self):
        for route in self:
            picking_types = route.rule_ids.picking_type_id
            route.applicable_flow_ids = self.env["stock.warehouse.flow"].search(
                [
                    ("from_picking_type_id", "in", picking_types.ids),
                ]
            )
