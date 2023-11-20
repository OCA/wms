# Copyright 2023 Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AttachmentSynchronizeTask(models.Model):
    _inherit = "attachment.synchronize.task"

    file_type = fields.Selection(
        selection_add=[
            ("export", "Export"),
            ("wms_reception_confirmed", "Reception confirmed"),
            ("wms_delivery_confirmed", "Delivery confirmed"),
        ]
    )
