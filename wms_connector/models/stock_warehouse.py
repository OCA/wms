# Copyright 2023 Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

FILTER_FIELDNAMES = [
    "wms_export_product_filter_id",
    "wms_product_sync_filter_id",
    "wms_export_picking_in_filter_id",
    "wms_export_picking_out_filter_id",
]
MAPPINGS = {
    "export": {
        "fieldname_task": "wms_export_task_id",
        "fieldname_cron": "wms_export_cron_id",
        "filetype": "export",
        "name_fragment": "exports (products, awaiting receptions, preparation orders",
        "code": "wh = env['stock.warehouse'].browse({0})\n"
        "wh.{1}.scheduler_export("
        '"wms.product.sync", wh._wms_domain_for("wms_product_sync")'
        ")\n"
        "wh.{1}.scheduler_export("
        '"stock.picking", wh._wms_domain_for("pickings_in")'
        ")\n"
        "wh.{1}.scheduler_export("
        '"stock.picking", wh._wms_domain_for("pickings_out")'
        ")",
    },
    "reception": {
        "fieldname_task": "wms_import_confirm_reception_task_id",
        "fieldname_cron": "wms_import_confirm_reception_cron_id",
        "filetype": "reception_confirmed",
        "name_fragment": "reception confirmation",
        "code": "env['stock.warehouse'].browse({}).{}.run_import()",
    },
    "delivery": {
        "fieldname_task": "wms_import_confirm_delivery_task_id",
        "fieldname_cron": "wms_import_confirm_delivery_cron_id",
        "filetype": "delivery_confirmed",
        "name_fragment": "delivery confirmation",
        "code": "env['stock.warehouse'].browse({}).{}.run_import()",
    },
}


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
    wms_product_sync_filter_id = fields.Many2one(
        "ir.filters",
    )
    wms_export_product_filter_id = fields.Many2one(
        "ir.filters",
    )
    wms_export_picking_in_filter_id = fields.Many2one(
        "ir.filters",
    )
    wms_export_picking_out_filter_id = fields.Many2one(
        "ir.filters",
    )
    wms_product_sync_ids = fields.One2many("wms.product.sync", "warehouse_id")

    def _wms_domain_for(self, model_domain):
        domains = {
            "wms_product_sync": [("warehouse_id", "=", self.id)]
            + self.wms_product_sync_filter_id._get_eval_domain(),
            "pickings_in": self.wms_export_picking_in_filter_id._get_eval_domain(),
            "pickings_out": self.wms_export_picking_out_filter_id._get_eval_domain(),
        }
        return domains[model_domain]

    def _inverse_active_wms_sync(self):
        for rec in self:
            if rec.active_wms_sync:
                rec._activate_crons_tasks()
            else:
                rec._deactivate_crons_tasks()

    def _activate_crons_tasks(self):
        for rec in self:
            for mappings in MAPPINGS.values():
                task_field_name = mappings["fieldname_task"]
                task = rec[task_field_name]
                if task:
                    task.active = True
                else:
                    rec[task_field_name] = self.env[
                        "attachment.synchronize.task"
                    ].create(
                        rec._prepare_wms_task_vals(
                            mappings["filetype"], mappings["name_fragment"]
                        )
                    )
                cron_field_name = mappings["fieldname_cron"]
                cron = rec[cron_field_name]
                if cron:
                    cron.active = True
                else:
                    code = mappings["code"].format(self.id, task_field_name)
                    rec[cron_field_name] = self.env["ir.cron"].create(
                        rec._prepare_wms_cron_vals(code, mappings["name_fragment"])
                    )
            for field in FILTER_FIELDNAMES:
                if not getattr(rec, field):
                    rec[field] = self.env.ref(
                        "wms_connector.default_{}".format(field[:-3])
                    )

    def _prepare_wms_task_vals(self, filetype, name_fragment=""):
        return {
            "name": "WMS task for {} {}".format(self.name, name_fragment),
            "method_type": "export",
            "filepath": "IN/",
            "backend_id": self.env.ref("storage_backend.default_storage_backend").id,
            "file_type": filetype,
        }

    def _prepare_wms_cron_vals(self, code="", name_fragment=""):
        return {
            "name": "WMS cron for {} {}".format(self.name, name_fragment),
            "active": False,
            "interval_type": "days",
            "interval_number": 1,
            "model_id": self.env.ref(
                "attachment_synchronize.model_attachment_synchronize_task"
            ).id,
            "state": "code",
            "code": code,
        }

    def _deactivate_crons_tasks(self):
        for rec in self:
            for mappings in MAPPINGS.values():
                rec[mappings["fieldname_task"]].active = False
                rec[mappings["fieldname_cron"]].active = False

    def refresh_wms_products(self):
        for rec in self:
            prd_with_sync = self.wms_product_sync_ids.product_id
            prd_matching = self.env["product.product"].search(
                rec.wms_export_product_filter_id
                and rec.wms_export_product_filter_id._get_eval_domain()
                or []
            )
            to_create = prd_matching - prd_with_sync
            for prd in to_create:
                self.env["wms.product.sync"].create(
                    {"product_id": prd.id, "warehouse_id": rec.id}
                )
            self.env["wms.product.sync"].search(
                [
                    ("warehouse_id", "=", rec.id),
                    ("product_id", "in", (prd_with_sync - prd_matching).ids),
                ]
            ).unlink()

    def button_open_wms_sync_ids(self):
        return {
            "name": "WMS synchronized products",
            "view_mode": "tree,form",
            "views": [
                (self.env.ref("wms_connector.wms_product_sync_tree_view").id, "tree"),
                (self.env.ref("wms_connector.wms_product_sync_form_view").id, "form"),
            ],
            "res_model": "wms.product.sync",
            "type": "ir.actions.act_window",
            "target": "current",
            "domain": self._wms_domain_for("wms_product_sync"),
        }

    def button_open_wms_pickings_in(self):
        return {
            "name": "WMS synchronized transfers",
            "view_mode": "tree,form",
            "views": [
                (False, "tree"),
                (False, "form"),
            ],
            "res_model": "stock.picking",
            "type": "ir.actions.act_window",
            "target": "current",
            "domain": self._wms_domain_for("pickings_in"),
        }

    def button_open_wms_pickings_out(self):
        return {
            "name": "WMS synchronized transfers",
            "view_mode": "tree,form",
            "views": [
                (False, "tree"),
                (False, "form"),
            ],
            "res_model": "stock.picking",
            "type": "ir.actions.act_window",
            "target": "current",
            "domain": self._wms_domain_for("pickings_out"),
        }
