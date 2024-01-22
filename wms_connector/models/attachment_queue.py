# Copyright 2023 Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

WMS_IMPORT_FILETYPES = [
    ("wms_reception_confirmed", "WMS Reception confirmed"),
    ("wms_delivery_confirmed", "WMS Delivery confirmed"),
    ("wms_update_inventory", "WMS inventory update"),
]


class AttachmentQueue(models.Model):
    _inherit = "attachment.queue"

    file_type = fields.Selection(selection_add=WMS_IMPORT_FILETYPES)
    default_warehouse_id = fields.Many2one(
        "stock.warehouse", compute="_compute_default_warehouse", store=True
    )

    def _compute_default_warehouse(self):
        for rec in self:
            task_queue_prefix = None
            if rec.file_type == "wms_reception_confirmed":
                task_queue_prefix = "wms_import_picking_in"
            elif rec.file_type == "wms_delivery_confirmed":
                task_queue_prefix = "wms_import_picking_out"
            elif rec.file_type == "wms_update_inventory":
                task_queue_prefix = "wms_import_update_inventory"

            if task_queue_prefix is not None:
                rec.default_warehouse_id = rec.env["stock.warehouse"].search(
                    [(f"{task_queue_prefix}_task_id.attachment_ids", "=", rec.id)]
                )

    def _run(self):
        for filetype in [el[0] for el in WMS_IMPORT_FILETYPES]:
            if self.file_type == filetype:
                return getattr(self, "_run_" + filetype)()
        return super()._run()

    def _run_wms_reception_confirmed(self):
        raise NotImplementedError

    def _run_wms_delivery_confirmed(self):
        raise NotImplementedError

    def _run_wms_update_inventory(self):
        raise NotImplementedError
