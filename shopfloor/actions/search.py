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

    def location_from_scan(self, barcode, limit=1):
        model = self.env["stock.location"]
        if not barcode:
            return model.browse()
        # First search location by barcode
        res = model.search([("barcode", "=", barcode)], limit=limit)
        # And only if we have not found through barcode search on the location name
        if len(res) < limit:
            res |= model.search([("name", "=", barcode)], limit=(limit - len(res)))
        return res

    def package_from_scan(self, barcode):
        model = self.env["stock.quant.package"]
        if not barcode:
            return model.browse()
        return model.search([("name", "=", barcode)], limit=1)

    def picking_from_scan(self, barcode, use_origin=False):
        model = self.env["stock.picking"]
        if not barcode:
            return model.browse()
        picking = model.search([("name", "=", barcode)], limit=1)
        # We need to split the domain in two different searches
        # as there might be a case where
        # the name of a picking is the same as the origin of another picking
        # (e.g. in a backorder) and we need to make sure
        # the name search takes priority.
        if picking:
            return picking
        if use_origin:
            source_document_domain = [
                # We could have the same origin for multiple transfers
                # but we're interested only in the "assigned" ones.
                ("origin", "=", barcode),
                ("state", "=", "assigned"),
            ]
            return model.search(source_document_domain)
        return model.browse()

    def product_from_scan(self, barcode):
        model = self.env["product.product"]
        if not barcode:
            return model.browse()
        return model.search([("barcode", "=", barcode)], limit=1)

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
