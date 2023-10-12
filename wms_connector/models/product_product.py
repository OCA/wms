# Copyright 2023 Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    wms_sync_ids = fields.One2many("wms.product.sync", "product_id")

