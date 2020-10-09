# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.addons.component.core import Component


class SearchAction(Component):
    """Provide methods to search records from scanner

    The methods should be used in Service Components, so a search will always
    have the same result in all scenarios.
    """

    _name = "shopfloor.search.action"
    _inherit = "shopfloor.process.action"
    _usage = "search"

    def location_from_scan(self, barcode):
        if not barcode:
            return self.env["stock.location"].browse()
        return self.env["stock.location"].search([("barcode", "=", barcode)])

    def package_from_scan(self, barcode):
        return self.env["stock.quant.package"].search([("name", "=", barcode)])

    def picking_from_scan(self, barcode):
        return self.env["stock.picking"].search([("name", "=", barcode)])

    def product_from_scan(self, barcode):
        product = self.env["product.product"].search([("barcode", "=", barcode)])
        if not product:
            packaging = self.env["product.packaging"].search(
                [("product_id", "!=", False), ("barcode", "=", barcode)]
            )
            product = packaging.product_id
        return product

    def lot_from_scan(self, barcode):
        return self.env["stock.production.lot"].search([("name", "=", barcode)])

    def generic_packaging_from_scan(self, barcode):
        return self.env["product.packaging"].search(
            [("barcode", "=", barcode), ("product_id", "=", False)]
        )
