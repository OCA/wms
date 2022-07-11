# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields, models


class StockWarehouse(models.Model):
    _inherit = "stock.warehouse"

    flow_ids = fields.One2many(
        comodel_name="stock.warehouse.flow",
        inverse_name="warehouse_id",
        string="Flows",
    )

    def action_view_all_flows(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "stock_warehouse_flow.stock_warehouse_flow_action"
        )
        action["domain"] = [("id", "in", self.flow_ids.ids)]
        action["context"] = {"default_warehouse_id": self.id}
        return action
