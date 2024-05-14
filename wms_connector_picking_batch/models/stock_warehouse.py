from copy import deepcopy

from odoo import api, fields, models

FILTER_VALS = {
    "wms_export_batch_picking_in_filter_id": {
        "name": "WMS: {} filter for picking batch in",
        "model_id": "stock.picking.batch",
    },
    "wms_export_batch_picking_out_filter_id": {
        "name": "WMS: {} filter for picking batch out",
        "model_id": "stock.picking.batch",
    },
}
# Find a better way to override filters
FILTER_DOMAINS = {
    "wms_export_picking_in_filter_id": [("batch_id", "=", False)],
    "wms_export_picking_out_filter_id": [("batch_id", "=", False)],
    "wms_export_batch_picking_in_filter_id": [
        ("wms_export_date", "=", False),
        ("picking_type_id", "=", {}),
        ("state", "=", "in_progress"),
    ],
    "wms_export_batch_picking_out_filter_id": [
        ("wms_export_date", "=", False),
        ("picking_type_id", "=", {}),
        ("state", "=", "in_progress"),
    ],
}


MAPPINGS = {
    "export_batch_pickings_in": {
        "fieldname_task": "wms_export_task_id",
        "fieldname_cron": "wms_export_batch_picking_in_cron_id",
        "filetype": "export",
        "method_type": "export",
        "filepath": "IN/",
        "name_fragment": "export batch pickings in",
        "code": "wh = env['stock.warehouse'].browse({})\n"
        "env['stock.picking.batch'].with_context(attachment_task=wh.{})._schedule_export(wh,"
        "domain=wh._wms_domain_for('batch_pickings_in')),",
    },
    "export_batch_pickings_out": {
        "fieldname_task": "wms_export_task_id",
        "fieldname_cron": "wms_export_batch_picking_out_cron_id",
        "filetype": "export",
        "method_type": "export",
        "filepath": "IN/",
        "name_fragment": "export batch pickings out",
        "code": "wh = env['stock.warehouse'].browse({})\n"
        "env['stock.picking.batch'].with_context(attachment_task=wh.{})._schedule_export(wh,"
        "domain=wh._wms_domain_for('batch_pickings_out')),",
    },
}


class StockWarehouse(models.Model):
    _inherit = "stock.warehouse"
    _name = "stock.warehouse"

    wms_export_batch_picking_in_cron_id = fields.Many2one("ir.cron", readonly=True)
    wms_export_batch_picking_out_cron_id = fields.Many2one("ir.cron", readonly=True)
    wms_export_batch_picking_in_filter_id = fields.Many2one("ir.filters")
    wms_export_batch_picking_out_filter_id = fields.Many2one("ir.filters")

    def _get_domains(self):
        domains = super()._get_domains()
        domains.update(
            {
                "batch_pickings_in": self.wms_export_batch_picking_in_filter_id._get_eval_domain(),
                "batch_pickings_out": self.wms_export_batch_picking_out_filter_id._get_eval_domain(),
            }
        )
        return domains

    @api.model
    def _get_mappings(self):
        mappings = super()._get_mappings()
        mappings.update(MAPPINGS)
        return mappings

    @api.model
    def _get_filter_domains(self):
        filter_domains = deepcopy(super()._get_filter_domains())

        modified = []
        for k, v in FILTER_DOMAINS.items():
            if k in filter_domains:
                filter_domains[k] += v
                modified.append(k)

        filter_domains.update(
            {k: v for k, v in FILTER_DOMAINS.items() if k not in modified}
        )

        return filter_domains

    @api.model
    def _get_filter_vals(self):
        # TODO(franz) remove picking with batch id from the picking in and out filter
        filter_vals = super()._get_filter_vals()
        filter_vals.update(FILTER_VALS)
        return filter_vals

    def _activate_filters(self):
        super()._activate_filters()
        self.wms_export_batch_picking_in_filter_id.domain = str(
            self._get_filter_domains()["wms_export_batch_picking_in_filter_id"]
        ).format(self.in_type_id.id)
        self.wms_export_batch_picking_out_filter_id.domain = str(
            self._get_filter_domains()["wms_export_batch_picking_out_filter_id"]
        ).format(self.out_type_id.id)

    def button_open_wms_batch_pickings_in(self):
        return {
            "name": "WMS synchronized transfers",
            "view_mode": "tree,form",
            "views": [
                (False, "tree"),
                (False, "form"),
            ],
            "res_model": "stock.picking.batch",
            "type": "ir.actions.act_window",
            "target": "current",
            "domain": self._wms_domain_for("batch_pickings_in"),
        }

    def button_open_wms_batch_pickings_out(self):
        return {
            "name": "WMS synchronized transfers",
            "view_mode": "tree,form",
            "views": [
                (False, "tree"),
                (False, "form"),
            ],
            "res_model": "stock.picking.batch",
            "type": "ir.actions.act_window",
            "target": "current",
            "domain": self._wms_domain_for("batch_pickings_out"),
        }
