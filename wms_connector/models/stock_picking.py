# Copyright 2023 Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = ["synchronize.exportable.mixin", "stock.picking"]
    _name = "stock.picking"

    wms_connector_exported = fields.Boolean(
        String="Exported to WMS",
        compute="_compute_wms_exported",
        readonly=True,
        store=True,
    )
    is_wms_exportable = fields.Boolean(
        compute="_compute_is_wms_exportable", readonly=True, store=True
    )

    @api.depends("wms_export_attachment")
    def _compute_wms_exported(self):
        for rec in self:
            rec.wms_connector_exported = bool(rec.wms_export_attachment)

    @api.depends("picking_type_id.warehouse_id.active_wms_sync")
    def _compute_is_wms_exportable(self):
        for rec in self:
            rec.is_wms_exportable = rec.picking_type_id.warehouse_id.active_wms_sync

    def action_show_export(self):
        self.ensure_one()
        return {
            "name": "WMS export",
            "type": "ir.actions.act_window",
            "res_model": "attachment.queue",
            "view_mode": "form",
            "res_id": self.wms_export_attachment.id,
        }
