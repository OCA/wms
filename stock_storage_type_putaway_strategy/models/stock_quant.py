# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import _, models, api
from odoo.exceptions import ValidationError


class StockQuant(models.Model):

    _inherit = 'stock.quant'

    @api.constrains('package_id', 'location_id', 'lot_id', 'product_id')
    def _check_storage_type(self):
        """
        Check if at least one location storage type allows the package storage
        type into the quant's location
        """
        for quant in self:
            location = quant.location_id
            pack_storage_type = quant.package_id.package_storage_type_id
            loc_storage_types = location.allowed_location_storage_type_ids
            if (
                not quant.package_id
                or not pack_storage_type
                or not loc_storage_types
            ):
                continue
            lst_allowed_for_pst = loc_storage_types.filtered(
                lambda lst: pack_storage_type in lst.package_storage_type_ids
            )
            if not lst_allowed_for_pst:
                raise ValidationError(
                    _(
                        "Package storage type %s is not allowed into "
                        "Location %s"
                    ) % (pack_storage_type, location)
                )
            allowed = False
            package_quants = quant.package_id.mapped('quant_ids')
            package_products = package_quants.mapped('product_id')
            package_lots = package_quants.mapped('lot_id')
            other_quants_in_location = self.search(
                [
                    ('location_id', '=', location.id),
                    ('id', 'not in', package_quants.ids)
                ]
            )
            products_in_location = other_quants_in_location.mapped(
                'product_id'
            )
            lots_in_location = other_quants_in_location.mapped('lot_id')
            for loc_storage_type in lst_allowed_for_pst:
                # Check content constraints
                if loc_storage_type.only_empty and other_quants_in_location:
                    continue
                if (
                    loc_storage_type.do_not_mix_products and (
                        len(package_products) > 1 or
                        package_products != products_in_location
                    )
                ):
                    continue
                if (
                    loc_storage_type.do_not_mix_lots and (
                        len(package_lots) > 1 or
                        package_lots != lots_in_location
                    )
                ):
                    continue
                # Check size constraint
                if (
                    loc_storage_type.max_height and
                    quant.package_id.height > loc_storage_type.max_height
                ):
                    continue
                if (
                    loc_storage_type.max_weight and
                    quant.package_id.pack_weight > loc_storage_type.max_weight
                ):
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
                        "package storage type %s into it."
                    ) % (
                        quant.package_id, location, pack_storage_type
                    )
                )
