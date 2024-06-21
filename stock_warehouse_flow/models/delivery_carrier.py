# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields, models


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    flow_ids = fields.Many2many(
        comodel_name="stock.warehouse.flow",
        relation="delivery_carrier_stock_warehouse_flow_rel",
        column1="delivery_carrier_id",
        column2="stock_warehouse_flow_id",
        string="Routing flows",
        copy=False,
    )

    def action_view_flows(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "stock_warehouse_flow.stock_warehouse_flow_action"
        )
        action["domain"] = [("id", "in", self.flow_ids.ids)]
        action["context"] = {"default_carrier_ids": [(6, 0, self.ids)]}
        return action
