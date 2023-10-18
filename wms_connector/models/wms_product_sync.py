# Copyright 2023 Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class WmsProductSync(models.Model):
    _inherit = ["synchronize.exportable.mixin"]
    _name = "wms.product.sync"
    _description = "Wms Product Sync"

    name = fields.Char(related="product_id.name")
    product_id = fields.Many2one("product.product", required=True)
    warehouse_id = fields.Many2one("stock.warehouse", required=True)
