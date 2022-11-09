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
            allowed = False
            package_weight_kg = (
                quant.package_id.pack_weight_in_kg
                or quant.package_id.estimated_pack_weight_kg
            )
            package_quants = quant.package_id.mapped("quant_ids")
            package_products = package_quants.mapped("product_id")
            package_lots = package_quants.mapped("lot_id")
            other_quants_in_location = self.search(
                [
                    ("location_id", "=", location.id),
                    ("id", "not in", package_quants.ids),
                    ("quantity", ">", 0),
                ]
            )
            products_in_location = other_quants_in_location.mapped("product_id")
            lots_in_location = other_quants_in_location.mapped("lot_id")
            capacity_fails = []
            for capacity in allowed_capacities:
                # Check content constraints
                if capacity.allow_new_product == "empty" and other_quants_in_location:
                    capacity_fails.append(
                        _(
                            "Storage Capacity {storage_capacity} is flagged "
                            "'only empty'"
                            " with other quants in location."
                        ).format(storage_capacity=capacity.display_name)
                    )
                    continue
                if capacity.allow_new_product == "same" and (
                    len(package_products) > 1
                    or len(products_in_location) >= 1
                    and package_products != products_in_location
                ):
                    capacity_fails.append(
                        _(
                            "Storage Capacity {storage_capacity} is flagged 'do not mix"
                            " products' but there are other products in "
                            "location."
                        ).format(storage_capacity=capacity.display_name)
                    )
                    continue
                if capacity.allow_new_product == "same_lot" and (
                    len(package_lots) > 1
                    or len(lots_in_location) >= 1
                    and package_lots != lots_in_location
                ):
                    capacity_fails.append(
                        _(
                            "Storage Capacity {storage_capacity} is flagged 'do not mix"
                            " lots' but there are other lots in "
                            "location."
                        ).format(storage_capacity=capacity.display_name)
                    )
                    continue
                # Check size constraint
                if (
                    capacity.storage_category_id.max_height_in_m
                    and quant.package_id.height_in_m
                    > capacity.storage_category_id.max_height_in_m
                ):
                    capacity_fails.append(
                        _(
                            "Storage Category {storage_category} defines "
                            "max height of {max_h} but the package is bigger: "
                            "{height}."
                        ).format(
                            storage_category=capacity.storage_category_id.display_name,
                            max_h=capacity.storage_category_id.max_height_in_m,
                            height=quant.package_id.height_in_m,
                        )
                    )
                    continue
                if (
                    capacity.storage_category_id.max_weight_in_kg
                    and package_weight_kg
                    > capacity.storage_category_id.max_weight_in_kg
                ):
                    capacity_fails.append(
                        _(
                            "Storage Category {storage_category} defines "
                            "max weight of {max_w} but the package is heavier: "
                            "{weight_kg}."
                        ).format(
                            storage_category=capacity.storage_category_id.display_name,
                            max_w=capacity.storage_category_id.max_weight_in_kg,
                            weight_kg=package_weight_kg,
                        )
                    )
                    continue
                # If we get here, it means there is a location storage type
                #  allowing the package into the location
                allowed = True
                break
            if not allowed:
                raise ValidationError(
                    _(
                        "Package {package} is not allowed into location {location},"
                        " because there isn't any storage capacity that allows"
                        " package type {type} into it:\n\n{fails}"
                    ).format(
                        package=quant.package_id.name,
                        location=location.complete_name,
                        type=package_type.name,
                        fails="\n".join(capacity_fails),
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
