# Copyright 2023 Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockWarehouse(models.Model):
    _inherit = "stock.warehouse"

    active_wms_sync = fields.Boolean(
        inverse="_inverse_active_wms_sync", readonly=False, store=True
    )
    sync_task_id = fields.Many2one("attachment.synchronize.task", readonly=True)
    sync_cron_id = fields.Many2one("ir.cron", readonly=True)

    def _inverse_active_wms_sync(self):
        for rec in self:
            if rec.active_wms_sync:
                rec._activate_cron_attachment_task()
            else:
                rec._deactivate_cron_attachment_task()

    def _activate_crons_attachment_queues(self):
        if self.sync_task_id and self.sync_cron_id:
            self.sync_task_id.active = True
            self.sync_cron_id.active = True
        else:
            self.sync_task_id = self.env["attachment.synchronize.task"].create(
                {
                    "name": "WMS Sync {}".format(self.name),
                    "method_type": "export",
                    "filepath": "OUT/",
                    "backend_id": self.env.ref(
                        "storage_backend.default_storage_backend"
                    ),
                }
            )
            self.sync_cron_id = self.env["ir.cron"].create(
                {
                    "name": "WMS Sync {}".format(self.name),
                    "active": False,
                    "interval_type": "days",
                    "interval_number": 1,
                    "model_id": self.env.ref(
                        "attachment_synchronize.model_attachment_synchronize_task"
                    ).id,
                    "state": "code",
                    "code": "",
                }
            )

    def _deactivate_cron_attachment_task(self):
        self.sync_task_id.active = False
        self.sync_cron_id.active = False

    def action_open_flows(self):
        raise NotImplementedError
        return {"type": "ir.action"}
