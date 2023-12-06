# Copyright 2023 Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AttachmentSynchronizeTask(models.Model):
    _inherit = "attachment.synchronize.task"

    default_warehouse_id = fields.Many2one("stock.warehouse")

    file_type = fields.Selection(
        selection_add=[
            ("export", "Export"),
            ("wms_reception_confirmed", "Reception confirmed"),
            ("wms_delivery_confirmed", "Delivery confirmed"),
            ("wms_update_inventory", "Inventory update"),
        ]
    )

    def _prepare_attachment_vals(self, data, filename):
        self.ensure_one()
        vals = super()._prepare_attachment_vals(data, filename)
        vals["default_warehouse_id"] = self.default_warehouse_id.id
        return vals
