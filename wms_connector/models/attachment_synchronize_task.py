# Copyright 2023 Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields


class AttachmentSynchronizeTask(models.Model):
    _inherit = "attachment.synchronize.task"

    def scheduler_export(self, model, domain=False):
        if not domain:
            recs = self.env[model].search([])
        else:
            recs = self.env[model].search(domain)
        if not recs:
            return
        attachments = recs.with_context(attachment_task=self).synchronize_export()
        attachments.run()

    file_type = fields.Selection(
        selection_add=[
            ("export", "Export"),
            ("reception_confirmed", "Reception confirmed"),
            ("delivery_confirmed", "Delivery confirmed"),
        ]
    )
