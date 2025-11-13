# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import _, api, models
from odoo.exceptions import ValidationError


class StockQuant(models.Model):

    _inherit = "stock.quant"

    @api.constrains("package_id", "location_id", "lot_id", "product_id")
    def _check_storage_capacities(self):
        """
        Check if at least one storage capacity allows the package type
        into the quant's location
        """
        for quant in self:
            location = quant.location_id
            package_type = quant.package_id.package_type_id
            storage_capacities = location.computed_storage_category_id.capacity_ids
            if not quant.package_id or not package_type or not storage_capacities:
                continue
            allowed_capacities = storage_capacities.filtered(
                lambda capacity: package_type == capacity.package_type_id
            )
            if not allowed_capacities:
                raise ValidationError(
                    _(
                        "Package type {storage} is not allowed into "
                        "Location {location}"
                    ).format(storage=package_type.name, location=location.name)
                )
            package = quant.package_id
            package_weight_kg = (
                package.pack_weight_in_kg or package.estimated_pack_weight_kg
            )
            error = None
            category = location.computed_storage_category_id
            # Check size constraint
            if (
                category.max_height_in_m
                and quant.package_id.height_in_m > category.max_height_in_m
            ):
                error = _(
                    "Storage Category {category} defines "
                    "max height of {max_h} but the package is bigger: "
                    "{height}."
                ).format(
                    category=category.display_name,
                    max_h=category.max_height_in_m,
                    height=quant.package_id.height_in_m,
                )
            if (
                category.max_weight_in_kg
                and package_weight_kg > category.max_weight_in_kg
            ):
                error = _(
                    "Storage Category {category} defines "
                    "max weight of {max_w} but the package is heavier: "
                    "{weight_kg}."
                ).format(
                    category=category.display_name,
                    max_w=category.max_weight_in_kg,
                    weight_kg=package_weight_kg,
                )
            if error:
                raise ValidationError(
                    _(
                        "Package {package} is not allowed into location {location},"
                        " because there isn't any rules that allows"
                        " package type {type} into it:\n\n{error}"
                    ).format(
                        package=package.name,
                        location=location.complete_name,
                        type=package_type.name,
                        error=error,
                    )
                )

    def write(self, vals):
        res = super().write(vals)
        self._invalidate_package_level_allowed_location_dest_ids()
        return res

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        self._invalidate_package_level_allowed_location_dest_ids()
        return res

    def _invalidate_package_level_allowed_location_dest_ids(self):
        self.env["stock.package_level"].invalidate_model(
            fnames=["allowed_location_dest_ids"]
        )
