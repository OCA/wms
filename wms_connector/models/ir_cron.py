# Copyright 2023 Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class IrCron(models.Model):
    _inherit = "ir.cron"

    warehouse_export_ids = fields.One2many("stock.warehouse", "wms_export_cron_id")
    warehouse_import_confirm_reception_ids = fields.One2many(
        "stock.warehouse", "wms_import_confirm_reception_cron_id"
    )
    warehouse_import_confirm_delivery_ids = fields.One2many(
        "stock.warehouse", "wms_import_confirm_delivery_cron_id"
    )
    product_sync_ids = fields.One2many("wms.product.sync", "warehouse_id")
