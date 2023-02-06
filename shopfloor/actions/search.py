# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.component.core import Component


class SearchResult:

    __slots__ = ("record", "type", "code")

    def __init__(self, **kw) -> None:
        for k in self.__slots__:
            setattr(self, k, kw.get(k))

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: type={self.type} code={self.code}>"

    def __bool__(self):
        return self.type != "none" or bool(self.record)

    def __eq__(self, other):
        for k in self.__slots__:
            if not hasattr(other, k):
                return False
            if getattr(other, k) != getattr(self, k):
                return False
        return True

    @property
    def records(self):
        """In some cases we expect more than one records (eg: location limit > 1) or lots"""
        return self.record if len(self.record) > 1 else None


class SearchAction(Component):
    """Provide methods to search records from scanner

    The methods should be used in Service Components, so a search will always
    have the same result in all scenarios.
    """

    _inherit = "shopfloor.search.action"

    @property
    def _barcode_type_handler(self):
        return {
            "product": self.product_from_scan,
            "package": self.package_from_scan,
            "picking": self.picking_from_scan,
            "location": self.location_from_scan,
            "location_dest": self.location_from_scan,
            "lot": self.lot_from_scan,
            "serial": self.lot_from_scan,
            "packaging": self.packaging_from_scan,
            "delivery_packaging": self.generic_packaging_from_scan,
        }

    def _make_search_result(self, **kwargs):
        """Build a 'SearchResult' object describing the record found.

        If no record has been found, the SearchResult object will have
        its 'type' defined to "none".
        """
        return SearchResult(**kwargs)

    def find(self, barcode, types=None, handler_kw=None):
        """Find Odoo record matching given `barcode`.

        Plain barcodes
        """
        barcode = barcode or ""
        return self.generic_find(barcode, types=types, handler_kw=handler_kw)

    def generic_find(self, barcode, types=None, handler_kw=None):
        handler_kw = handler_kw or {}
        _types = types or self._barcode_type_handler.keys()
        # TODO: decide the best default order in case we don't pass `types`
        for btype in _types:
            handler = self._barcode_type_handler[btype]
            record = handler(barcode, **handler_kw.get(btype, {}))
            if record:
                return self._make_search_result(record=record, code=barcode, type=btype)

        return self._make_search_result(type="none")

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
