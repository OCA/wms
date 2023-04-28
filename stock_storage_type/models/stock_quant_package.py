# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class StockQuantPackage(models.Model):

    _inherit = "stock.quant.package"

    pack_weight_in_kg = fields.Float(
        help="Technical field, to speed up comparaisons",
        compute="_compute_pack_weight_in_kg",
        store=True,
    )
    height_in_m = fields.Float(
        help="Technical field, to speed up comparaisons",
        compute="_compute_height_in_m",
        store=True,
    )

    @api.depends("pack_weight", "weight_uom_id")
    def _compute_pack_weight_in_kg(self):
        uom_kg = self.env.ref("uom.product_uom_kgm")
        for package in self:
            package.pack_weight_in_kg = package.weight_uom_id._compute_quantity(
                qty=package.pack_weight,
                to_unit=uom_kg,
                round=False,
            )

    @api.depends("height", "length_uom_id")
    def _compute_height_in_m(self):
        uom_meters = self.env.ref("uom.product_uom_meter")
        for package in self:
            package.height_in_m = package.length_uom_id._compute_quantity(
                qty=package.height,
                to_unit=uom_meters,
                round=False,
            )

    @api.constrains("height", "package_type_id", "product_packaging_id")
    def _check_package_type_height_required(self):
        for package in self:
            if package.package_type_id.height_required and not package.height:
                raise ValidationError(
                    _("The height is mandatory on package {}.").format(package.name)
                )

    def auto_assign_packaging(self):
        res = super().auto_assign_packaging()
        for package in self:
            if not package.package_type_id:
                # if no storage type could be set by auto assign,
                # fallback on the default product's storage type (if any)
                package._sync_package_type_from_single_product()
        return res

    @api.model_create_multi
    def create(self, vals):
        records = super().create(vals)
        records._sync_package_type_from_packaging()
        return records

    def write(self, vals):
        result = super().write(vals)
        if vals.get("product_packaging_id"):
            self._sync_package_type_from_packaging()
        return result

    def _sync_package_type_from_packaging(self):
        for package in self:
            if package.package_type_id:
                # Do not set package storage type for delivery packages
                # to not trigger constraint like height requirement
                # (we are delivering them, not storing them)
                continue
            package_type = package.product_packaging_id.package_type_id
            if not package_type:
                continue
            package.package_type_id = package_type

    def _sync_package_type_from_single_product(self):
        for package in self:
            if package.package_type_id:
                # Do not set package type for delivery packages
                # to not trigger constraint like height requirement
                # (we are delivering them, not storing them)
                continue
            package_type = package.single_product_id.package_type_id
            if not package_type:
                continue
            package.package_type_id = package_type
