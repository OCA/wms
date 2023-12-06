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
    # This seems fishy but we need the warehouse id to allow
    # for update inventory
    default_warehouse_id = fields.Many2one("stock.warehouse")

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
