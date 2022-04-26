# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.addons.component.core import Component


class SearchAction(Component):
    """Provide methods to search records from scanner

    The methods should be used in Service Components, so a search will always
    have the same result in all scenarios.
    """

    _inherit = "shopfloor.search.action"

    # TODO: these methods shall be probably replaced by scan anything handlers

    def location_from_scan(self, barcode):
        model = self.env["stock.location"]
        if not barcode:
            return model.browse()
        return model.search(
            ["|", ("barcode", "=", barcode), ("name", "=", barcode)], limit=1
        )

    def package_from_scan(self, barcode):
        model = self.env["stock.quant.package"]
        if not barcode:
            return model.browse()
        return model.search([("name", "=", barcode)], limit=1)

    def picking_from_scan(self, barcode):
        model = self.env["stock.picking"]
        if not barcode:
            return model.browse()
        return model.search([("name", "=", barcode)], limit=1)

    def product_from_scan(self, barcode, use_packaging=True):
        model = self.env["product.product"]
        if not barcode:
            return model.browse()
        product = model.search([("barcode", "=", barcode)], limit=1)
        if not product and use_packaging:
            packaging = self.packaging_from_scan(barcode)
            product = packaging.product_id
        return product

    def lot_from_scan(self, barcode, products=None, limit=1):
        model = self.env["stock.production.lot"]
        if not barcode:
            return model.browse()
        domain = [
            ("company_id", "=", self.env.company.id),
            ("name", "=", barcode),
        ]
        if products:
            domain.append(("product_id", "in", products.ids))
        return model.search(domain, limit=limit)

    def packaging_from_scan(self, barcode):
        model = self.env["product.packaging"]
        if not barcode:
            return model.browse()
        return model.search(
            [("barcode", "=", barcode), ("product_id", "!=", False)], limit=1
        )

    def generic_packaging_from_scan(self, barcode):
        model = self.env["product.packaging"]
        if not barcode:
            return model.browse()
        return model.search(
            [("barcode", "=", barcode), ("product_id", "=", False)], limit=1
        )
