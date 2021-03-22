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
            return self.env["product.packaging"].browse()
        return carrier[fname]

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
