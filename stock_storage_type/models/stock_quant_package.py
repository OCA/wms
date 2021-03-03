# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class StockQuantPackage(models.Model):

    _inherit = "stock.quant.package"

    package_storage_type_id = fields.Many2one(
        "stock.package.storage.type",
        help="Package storage type for put-away computation. Get value "
        "automatically from the packaging if set, or from the product if"
        "the package contains only a single product.",
    )

    @api.constrains("height", "package_storage_type_id", "product_packaging_id")
    def _check_storage_type_height_required(self):
        for package in self:
            if package.package_storage_type_id.height_required and not package.height:
                raise ValidationError(
                    _("The height is mandatory on package {}.").format(package.name)
                )

    def auto_assign_packaging(self):
        super().auto_assign_packaging()
        for package in self:
            if not package.package_storage_type_id:
                # if no storage type could be set by auto assign,
                # fallback on the default product's storage type (if any)
                package._sync_storage_type_from_single_product()

    @api.model_create_multi
    def create(self, vals):
        records = super().create(vals)
        records._sync_storage_type_from_packaging()
        return records

    def write(self, vals):
        result = super().write(vals)
        if vals.get("product_packaging_id"):
            self._sync_storage_type_from_packaging()
        return result

    def _sync_storage_type_from_packaging(self):
        for package in self:
            if package.packaging_id:
                # Do not set package storage type for delivery packages
                # to not trigger constraint like height requirement
                # (we are delivering them, not storing them)
                continue
            storage_type = package.product_packaging_id.package_storage_type_id
            if not storage_type:
                continue
            package.package_storage_type_id = storage_type

    def _sync_storage_type_from_single_product(self):
        for package in self:
            if package.packaging_id:
                # Do not set package storage type for delivery packages
                # to not trigger constraint like height requirement
                # (we are delivering them, not storing them)
                continue
            storage_type = package.single_product_id.product_package_storage_type_id
            if not storage_type:
                continue
            package.package_storage_type_id = storage_type
