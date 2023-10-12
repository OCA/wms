# Copyright 2023 Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

TASKS = [
    ("export", "exports (products, awaiting receptions, preparation orders"),
    ("import_confirm_reception", "reception confirmation"),
    ("import_confirm_delivery", "delivery confirmation"),
]
TASK_FIELDNAME = "wms_{}_task_id"
CRON_FIELDNAME = "wms_{}_cron_id"


class StockWarehouse(models.Model):
    _inherit = "stock.warehouse"

    active_wms_sync = fields.Boolean(
        inverse="_inverse_active_wms_sync", readonly=False, store=True
    )
    wms_export_task_id = fields.Many2one("attachment.synchronize.task", readonly=True)
    wms_import_confirm_reception_task_id = fields.Many2one(
        "attachment.synchronize.task", readonly=True
    )
    wms_import_confirm_delivery_task_id = fields.Many2one(
        "attachment.synchronize.task", readonly=True
    )
    wms_export_cron_id = fields.Many2one("ir.cron", readonly=True)
    wms_import_confirm_reception_cron_id = fields.Many2one("ir.cron", readonly=True)
    wms_import_confirm_delivery_cron_id = fields.Many2one("ir.cron", readonly=True)
    wms_product_filter_id = fields.Many2one(
        "ir.filters",
        default=lambda r: r.env.ref("wms_connector.default_empty_filter"),
    )
    wms_picking_ar_filter_id = fields.Many2one(
        "ir.filters",
        default=lambda r: r.env.ref("wms_connector.default_empty_filter"),
    )
    wms_picking_prp_filter_id = fields.Many2one(
        "ir.filters",
        default=lambda r: r.env.ref("wms_connector.default_empty_filter"),
    )
    wms_product_sync_ids = fields.One2many("product.product", "warehouse_id")

    def _inverse_active_wms_sync(self):
        for rec in self:
            if rec.active_wms_sync:
                rec._activate_crons_tasks()
            else:
                rec._deactivate_crons_tasks()

    def _activate_crons_tasks(self):
        for kind in TASKS:
            task_field_name = TASK_FIELDNAME.format(kind[0])
            task = getattr(self, task_field_name)
            if task:
                task.active = True
            else:
                setattr(
                    self,
                    task_field_name,
                    self.env["attachment.synchronize.task"].create(
                        {
                            "name": "WMS task for {} ({})".format(self.name, kind[1]),
                            "method_type": "export",
                            "filepath": "OUT/",
                            "backend_id": self.env.ref(
                                "storage_backend.default_storage_backend"
                            ),
                        }
                    ),
                )
            cron_field_name = CRON_FIELDNAME.format(kind[0])
            cron = getattr(self, cron_field_name)
            if cron:
                cron.active = True
            else:
                setattr(
                    self,
                    cron_field_name,
                    self.env["ir.cron"].create(
                        {
                            "name": "WMS cron for {} ({})".format(self.name, kind[1]),
                            "active": False,
                            "interval_type": "days",
                            "interval_number": 1,
                            "model_id": self.env.ref(
                                "attachment_synchronize.model_attachment_synchronize_task"
                            ).id,
                            "state": "code",
                            "code": "",  # TODO
                        }
                    ),
                )

    def _deactivate_crons_tasks(self):
        for kind in TASKS:
            setattr(self, TASK_FIELDNAME.format(kind[0]), False)
            setattr(self, CRON_FIELDNAME.format(kind[0]), False)

    def action_open_flows(self):
        raise NotImplementedError
        return {"type": "ir.action"}

    def refresh_wms_products(self):
        for rec in self:
            rec.wms_product_sync_ids.unlink()
            for prd in self.env["product.product"].search(
                rec.wms_product_filter_id._get_eval_domain()
            ):
                self.env["wms.product.sync"].create(
                    {"product_id": prd.id, "warehouse_id": rec.id}
                )
