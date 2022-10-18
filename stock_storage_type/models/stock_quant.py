# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import _, api, models
from odoo.exceptions import ValidationError


class StockQuant(models.Model):

    _inherit = "stock.quant"

    @api.constrains("package_id", "location_id", "lot_id", "product_id")
    def _check_storage_type(self):
        """
        Check if at least one location storage type allows the package storage
        type into the quant's location
        """
        for quant in self:
            location = quant.location_id
            pack_storage_type = quant.package_id.package_type_id
            loc_storage_types = location.allowed_location_storage_type_ids
            if not quant.package_id or not pack_storage_type or not loc_storage_types:
                continue
            lst_allowed_for_pst = loc_storage_types.filtered(
                lambda lst: pack_storage_type in lst.package_type_ids
            )
            if not lst_allowed_for_pst:
                raise ValidationError(
                    _(
                        "Package storage type {storage} is not allowed into "
                        "Location {location}"
                    ).format(storage=pack_storage_type.name, location=location.name)
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
            lst_fails = []
            for loc_storage_type in lst_allowed_for_pst:
                # Check content constraints
                if loc_storage_type.only_empty and other_quants_in_location:
                    lst_fails.append(
                        _(
                            "Location storage type {storage_type} is flagged "
                            "'only empty'"
                            " with other quants in location."
                        ).format(storage_type=loc_storage_type.name)
                    )
                    continue
                if loc_storage_type.do_not_mix_products and (
                    len(package_products) > 1
                    or len(products_in_location) >= 1
                    and package_products != products_in_location
                ):
                    lst_fails.append(
                        _(
                            "Location storage type {storage_type} is flagged 'do not mix"
                            " products' but there are other products in "
                            "location."
                        ).format(storage_type=loc_storage_type.name)
                    )
                    continue
                if loc_storage_type.do_not_mix_lots and (
                    len(package_lots) > 1
                    or len(lots_in_location) >= 1
                    and package_lots != lots_in_location
                ):
                    lst_fails.append(
                        _(
                            "Location storage type {storage_type} is flagged 'do not mix"
                            " lots' but there are other lots in "
                            "location."
                        ).format(storage_type=loc_storage_type.name)
                    )
                    continue
                # Check size constraint
                if (
                    loc_storage_type.max_height_in_m
                    and quant.package_id.height_in_m > loc_storage_type.max_height_in_m
                ):
                    lst_fails.append(
                        _(
                            "Location storage type {storage_type} defines "
                            "max height of {max_h} but the package is bigger: "
                            "{height}."
                        ).format(
                            storage_type=loc_storage_type.name,
                            max_h=loc_storage_type.max_height_in_m,
                            height=quant.package_id.height_in_m,
                        )
                    )
                    continue
                if (
                    loc_storage_type.max_weight_in_kg
                    and package_weight_kg > loc_storage_type.max_weight_in_kg
                ):
                    lst_fails.append(
                        _(
                            "Location storage type {storage_type} defines "
                            "max weight of {max_w} but the package is heavier: "
                            "{weight_kg}."
                        ).format(
                            storage_type=loc_storage_type.name,
                            max_w=loc_storage_type.max_weight_in_kg,
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
                        " because there isn't any location storage type that allows"
                        " package storage type {type} into it:\n\n{fails}"
                    ).format(
                        package=quant.package_id.name,
                        location=location.complete_name,
                        type=pack_storage_type.name,
                        fails="\n".join(lst_fails),
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
