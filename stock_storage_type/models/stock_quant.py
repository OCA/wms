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
            pack_storage_type = quant.package_id.package_storage_type_id
            loc_storage_types = location.allowed_location_storage_type_ids
            if not quant.package_id or not pack_storage_type or not loc_storage_types:
                continue
            lst_allowed_for_pst = loc_storage_types.filtered(
                lambda lst: pack_storage_type in lst.package_storage_type_ids
            )
            if not lst_allowed_for_pst:
                raise ValidationError(
                    _("Package storage type %s is not allowed into " "Location %s")
                    % (pack_storage_type.name, location.name)
                )
            allowed = False
            package_weight = (
                quant.package_id.pack_weight or quant.package_id.estimated_pack_weight
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
                            "Location storage type %s is flagged 'only empty'"
                            " with other quants in location." % loc_storage_type.name
                        )
                    )
                    continue
                if loc_storage_type.do_not_mix_products and (
                    len(package_products) > 1
                    or len(products_in_location) >= 1
                    and package_products != products_in_location
                ):
                    lst_fails.append(
                        _(
                            "Location storage type %s is flagged 'do not mix"
                            " products' but there are other products in "
                            "location." % loc_storage_type.name
                        )
                    )
                    continue
                if loc_storage_type.do_not_mix_lots and (
                    len(package_lots) > 1
                    or len(lots_in_location) >= 1
                    and package_lots != lots_in_location
                ):
                    lst_fails.append(
                        _(
                            "Location storage type %s is flagged 'do not mix"
                            " lots' but there are other lots in "
                            "location." % loc_storage_type.name
                        )
                    )
                    continue
                # Check size constraint
                if (
                    loc_storage_type.max_height
                    and quant.package_id.height > loc_storage_type.max_height
                ):
                    lst_fails.append(
                        _(
                            "Location storage type %s defines max height of %s"
                            " but the package is bigger: %s."
                            % (
                                loc_storage_type.name,
                                loc_storage_type.max_height,
                                quant.package_id.height,
                            )
                        )
                    )
                    continue
                if (
                    loc_storage_type.max_weight
                    and package_weight > loc_storage_type.max_weight
                ):
                    lst_fails.append(
                        _(
                            "Location storage type %s defines max weight of %s"
                            " but the package is heavier: %s."
                            % (
                                loc_storage_type.name,
                                loc_storage_type.max_weight,
                                package_weight,
                            )
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
                        "Package %s is not allowed into location %s, because "
                        "there isn't any location storage type that allows "
                        "package storage type %s into it:\n\n%s"
                    )
                    % (
                        quant.package_id.name,
                        location.complete_name,
                        pack_storage_type.name,
                        "\n".join(lst_fails),
                    )
                )

    def write(self, vals):
        res = super().write(vals)
        self._invalidate_package_level_allowed_location_dest_domain()
        return res

    @api.model
    def create(self, vals):
        res = super().create(vals)
        self._invalidate_package_level_allowed_location_dest_domain()
        return res

    def _invalidate_package_level_allowed_location_dest_domain(self):
        self.env["stock.package_level"].invalidate_cache(
            fnames=["allowed_location_dest_domain"]
        )
