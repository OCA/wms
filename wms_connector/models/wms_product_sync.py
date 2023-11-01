# Copyright 2023 Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class WmsProductSync(models.Model):
    _inherit = ["synchronize.exportable.mixin"]
    _name = "wms.product.sync"
    _description = "Wms Product Sync"

    name = fields.Char(
        related="product_id.name",
    )
    product_id = fields.Many2one("product.product", required=True, readonly=True)
    warehouse_id = fields.Many2one("stock.warehouse", required=True, readonly=True)
    active = fields.Boolean(default=True)

    to_export = fields.Boolean(compute="_compute_to_export", store=True, readonly=False)

    @api.depends("product_id.name", "active")
    def _compute_to_export(self):
        for record in self:
            record.to_export = True

    def _schedule_export(self, warehouse, domain=False):
        warehouse.refresh_wms_products()
        return super()._schedule_export(warehouse, domain)

    def track_export(self, attachment):
        super().track_export(attachment)
        self.to_export = False
