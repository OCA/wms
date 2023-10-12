# Copyright 2023 Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class WmsProductSync(models.Model):
    _inherit = ["synchronize.exportable.mixin"]
    _name = "wms.product.sync"
    _description = "Wms Product Sync"

    name = fields.Char()
    product_id = fields.Many2one("product.product")
    warehouse_id = fields.Many2one("stock.warehouse")
