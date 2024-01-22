# Copyright 2023 Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

WMS_IMPORT_FILETYPES = [
    ("wms_reception_confirmed", "WMS Reception confirmed"),
    ("wms_delivery_confirmed", "WMS Delivery confirmed"),
    ("wms_update_inventory", "WMS inventory update"),
]


class AttachmentQueue(models.Model):
    _inherit = "attachment.queue"

    file_type = fields.Selection(selection_add=WMS_IMPORT_FILETYPES)
    warehouse_id = fields.Many2one(
        "stock.warehouse",
        compute="_compute_warehouse",
    )
    picking_imported_count = fields.Integer(compute="_compute_picking_imported_count")
    picking_imported_ids = fields.One2many(
        "stock.picking", "wms_import_attachment_id", "Picking Imported"
    )

    @api.depends("picking_imported_ids")
    def _compute_picking_imported_count(self):
        for record in self:
            record.picking_imported_count = len(record.picking_imported_ids)

    def _compute_warehouse(self):
        for rec in self:
            field = None
            if rec.file_type == "wms_reception_confirmed":
                field = "wms_import_confirm_reception_task_id"
            elif rec.file_type == "wms_delivery_confirmed":
                field = "wms_import_confirm_delivery_task_id"
            elif rec.file_type == "wms_update_inventory":
                field = "wms_import_update_inventory_task_id"

            if field:
                rec.warehouse_id = self.env["stock.warehouse"].search(
                    [(field, "=", rec.task_id.id)]
                )

    def _run(self):
        for filetype in [el[0] for el in WMS_IMPORT_FILETYPES]:
            if self.file_type == filetype:
                return getattr(self.with_company(self.company_id), "_run_" + filetype)()
        return super()._run()

    def _run_wms_reception_confirmed(self):
        raise NotImplementedError

    def _run_wms_delivery_confirmed(self):
        raise NotImplementedError

    def _run_wms_update_inventory(self):
        raise NotImplementedError

    def button_open_imported_picking(self):
        self.ensure_one()
        action = self.env.ref("stock.action_picking_tree_all").sudo().read()[0]
        action["domain"] = [("wms_import_attachment_id", "=", self.id)]
        return action
