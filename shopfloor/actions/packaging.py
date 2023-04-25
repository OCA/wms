# Copyright 2021 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.addons.component.core import Component


class PackagingAction(Component):
    """Provide methods to work with packaging operations."""

    _name = "shopfloor.packaging.action"
    _inherit = "shopfloor.process.action"
    _usage = "packaging"

    def packaging_valid_for_carrier(self, packaging, carrier):
        return self.packaging_type_valid_for_carrier(packaging.package_type_id, carrier)

    def packaging_type_valid_for_carrier(self, packaging_type, carrier):
        return packaging_type.package_carrier_type in (
            "none",
            carrier.delivery_type,
        )

    def create_delivery_package(self, carrier):
        default_packaging = self._get_default_packaging(carrier)
        return self.create_package_from_packaging(default_packaging)

    def _get_default_packaging(self, carrier):
        # TODO: refactor `delivery_[carrier_name]` modules
        # to have always the same field named `default_packaging_id`
        # to unify lookup of this field.
        # As alternative add a computed field.
        # AFAIS there's no reason to have 1 field per carrier type.
        fname = carrier.delivery_type + "_default_packaging_id"
        if fname not in carrier._fields:
            return self.env["stock.package.type"].browse()
        return carrier[fname]

    def create_package_from_packaging(self, packaging=None):
        if packaging:
            vals = self._package_vals_from_packaging(packaging)
        else:
            vals = self._package_vals_without_packaging()
        return self.env["stock.quant.package"].create(vals)

    def _package_vals_from_packaging(self, packaging):
        return {
            "package_type_id": packaging.id,
            "pack_length": packaging.packaging_length,
            "width": packaging.width,
            "height": packaging.height,
        }

    def _package_vals_without_packaging(self):
        return {}

    def package_has_several_products(self, package):
        return len(package.quant_ids.product_id) > 1

    def package_has_several_lots(self, package):
        return len(package.quant_ids.lot_id) > 1

    def is_complete_mix_pack(self, package):
        """Check if a package is mixed and completely reserved.

        Will return true if the package has multiple distinct products and
        all the package quantities are reserved.
        """
        return self.package_has_several_products(package) and all(
            quant.quantity == quant.reserved_quantity for quant in package.quant_ids
        )
