# Copyright 2021 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.addons.component.core import Component


class PackagingAction(Component):
    """Provide methods to work with packaging operations."""

    _name = "shopfloor.packaging.action"
    _inherit = "shopfloor.process.action"
    _usage = "packaging"

    def packaging_valid_for_carrier(self, packaging, carrier):
        return packaging.package_carrier_type in ("none", carrier.delivery_type)

    def create_delivery_package(self, carrier):
        delivery_type = carrier.delivery_type
        # TODO: refactor `delivery_[carrier_name]` modules
        # to have always the same field named `default_packaging_id`
        # to unify lookup of this field.
        # As alternative add a computed field.
        default_packaging = carrier[delivery_type + "_default_packaging_id"]
        return self.create_package_from_packaging(default_packaging)

    def create_package_from_packaging(self, packaging=None):
        if packaging:
            vals = self._package_vals_from_packaging(packaging)
        else:
            vals = self._package_vals_without_packaging()
        return self.env["stock.quant.package"].create(vals)

    def _package_vals_from_packaging(self, packaging):
        return {
            "packaging_id": packaging.id,
            "lngth": packaging.lngth,
            "width": packaging.width,
            "height": packaging.height,
        }

    def _package_vals_without_packaging(self):
        return {}
