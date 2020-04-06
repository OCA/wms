# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import api, fields, models


class StockQuantPackage(models.Model):

    _inherit = "stock.quant.package"

    package_storage_type_id = fields.Many2one("stock.package.storage.type")

    @api.onchange("product_packaging_id")
    def onchange_product_packaging_id(self):
        res = super().onchange_product_packaging_id()
        packaging = self.product_packaging_id
        storage_type = packaging.package_storage_type_id
        if storage_type:
            self.package_storage_type_id = storage_type
        return res

    @api.model
    def create(self, vals):
        vals = self._vals_for_storage_type(vals)
        return super().create(vals)

    def write(self, vals):
        vals = self._vals_for_storage_type(vals)
        return super().write(vals)

    def _vals_for_storage_type(self, vals):
        packaging_id = vals.get("product_packaging_id")
        if packaging_id:
            packaging = self.env["product.packaging"].browse(packaging_id)
            storage_type = packaging.package_storage_type_id
            if storage_type:
                vals = dict(vals, package_storage_type_id=storage_type.id)
        return vals
