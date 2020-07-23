# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import api, fields, models


class StockQuantPackage(models.Model):

    _inherit = "stock.quant.package"

    package_storage_type_id = fields.Many2one(
        "stock.package.storage.type",
        compute="_compute_package_storage_type_id",
        store=True,
        readonly=False,
        help="Package storage type for put-away computation. Computed "
        "automatically from the packaging if set, or from the product if"
        "the package contains only a single product.",
    )

    @api.depends(
        "product_packaging_id",
        "product_packaging_id.package_storage_type_id",
        "quant_ids",
        "quant_ids.product_id",
        "quant_ids.product_id.product_package_storage_type_id",
    )
    def _compute_package_storage_type_id(self):
        for pack in self:
            if pack.package_storage_type_id:
                continue
            elif (
                pack.product_packaging_id
                and pack.product_packaging_id.package_storage_type_id
            ):
                pack.package_storage_type_id = (
                    pack.product_packaging_id.package_storage_type_id
                )
            elif (
                pack.single_product_id
                and pack.single_product_id.product_package_storage_type_id
            ):
                pack.package_storage_type_id = (
                    pack.single_product_id.product_package_storage_type_id
                )
            else:
                pack.package_storage_type_id = False
