# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# Copyright 2024 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.osv.expression import AND

from odoo.addons.component.core import Component


class SearchResult:
    __slots__ = ("record", "type", "code", "parse_result")

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
        # In some cases we expect more than one records
        # (eg: location limit > 1) or lots
        return self.record if len(self.record) > 1 else None


class SearchAction(Component):
    """Provide methods to search records from scanner

    The methods should be used in Service Components, so a search will always
    have the same result in all scenarios.
    """

    _inherit = "shopfloor.search.action"

    @property
    def parser(self):
        parser = self._actions_for("barcode")
        parser.search_action = self
        return parser

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._products = None
        self._limit = 1
        self._use_origin = False
        self._extra_domain = None

    def for_products(self, products):
        self._products = products
        return self

    def with_limit(self, limit):
        self._limit = limit
        return self

    def with_origin(self, use_origin=True):
        self._use_origin = use_origin
        return self

    def with_domain(self, extra_domain):
        self._extra_domain = extra_domain
        return self

    @property
    def _barcode_type_handler(self):
        return {
            "product": self._find_product,
            "package": self._find_package,
            "picking": self._find_picking,
            "location": self._find_location,
            "location_dest": self._find_location,
            "lot": self._find_lot,
            "serial": self._find_lot,
            "packaging": self._find_packaging,
            "delivery_packaging": self._find_delivery_packaging,
            "origin_move": self._find_origin_move,
            # Extra data can be contained in barcodes
            "expiration_date": self._find_expiration_date,
        }

    def _make_search_result(self, **kwargs):
        """Build a 'SearchResult' object describing the record found.

        If no record has been found, the SearchResult object will have
        its 'type' defined to "none".
        """
        return SearchResult(**kwargs)

    def _get_parse_results_value(self, parse_results: dict, btype: str):
        result = parse_results.get(btype) or parse_results.get("unknown")
        return result.value if result else None

    def find(self, barcode, types=None):
        """Find Odoo record matching given `barcode`.

        Plain barcodes
        """
        barcode = barcode or ""
        return self.generic_find(barcode, types=types)

    def _find_record_by_type(self, parse_results, btype):
        handler = self._barcode_type_handler.get(btype)
        if not handler:
            return
        return handler(parse_results, btype=btype)

    def generic_find(self, barcode, types=None):
        # TODO: decide the best default order in case we don't pass `types`
        types = types or self._barcode_type_handler.keys()

        parse_results = self.parser.parse(barcode)

        for btype in types:
            record = self._find_record_by_type(parse_results, btype)
            if record:
                return self._make_search_result(
                    record=record,
                    code=barcode,
                    type=btype,
                    parse_result=parse_results,
                )
        return self._make_search_result(type="none", parse_result=parse_results)

    # -------------------------------------------------------------------------
    # Public Entry Points (Safe for direct downstream calls)
    # -------------------------------------------------------------------------

    def location_from_scan(self, barcode):
        res = self.generic_find(barcode, types=["location", "location_dest"])
        return res.record if res else self.env["stock.location"].browse()

    def package_from_scan(self, barcode):
        res = self.generic_find(barcode, types=["package"])
        return res.record if res else self.env["stock.quant.package"].browse()

    def picking_from_scan(self, barcode):
        res = self.generic_find(barcode, types=["picking"])
        return res.record if res else self.env["stock.picking"].browse()

    def product_from_scan(self, barcode):
        res = self.generic_find(barcode, types=["product"])
        return res.record if res else self.env["product.product"].browse()

    def lot_from_scan(self, barcode):
        res = self.generic_find(barcode, types=["lot", "serial"])
        return res.record if res else self.env["stock.lot"].browse()

    def packaging_from_scan(self, barcode):
        res = self.generic_find(barcode, types=["packaging"])
        return res.record if res else self.env["product.packaging"].browse()

    def delivery_packaging_from_scan(self, barcode):
        res = self.generic_find(barcode, types=["delivery_packaging"])
        return res.record if res else self.env["stock.package.type"].browse()

    def origin_move_from_scan(self, barcode):
        res = self.generic_find(barcode, types=["origin_move"])
        return res.record if res else self.env["stock.move"].browse()

    def expiration_date_from_scan(self, barcode):
        res = self.generic_find(barcode, types=["expiration_date"])
        return res.record if res else None

    # -------------------------------------------------------------------------
    # Internal Concrete DB Search Methods
    # -------------------------------------------------------------------------

    def _find_location(self, parse_results, btype="location"):
        model = self.env["stock.location"]
        barcode = self._get_parse_results_value(parse_results, btype)
        if not barcode:
            return model.browse()
        # First search location by barcode
        res = model.search([("barcode", "=", barcode)], limit=self._limit)
        # And only if we have not found through barcode search on the location name
        if len(res) < self._limit:
            res |= model.search(
                [("name", "=", barcode)], limit=(self._limit - len(res))
            )
        return res

    def _find_package(self, parse_results, btype="package"):
        model = self.env["stock.quant.package"]
        barcode = self._get_parse_results_value(parse_results, btype)
        if not barcode:
            return model.browse()
        return model.search([("name", "=", barcode)], limit=1)

    def _find_picking(self, parse_results, btype="picking"):
        model = self.env["stock.picking"]
        barcode = self._get_parse_results_value(parse_results, btype)
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
        if self._use_origin:
            source_document_domain = [
                # We could have the same origin for multiple transfers
                # but we're interested only in the "assigned" ones.
                ("origin", "=", barcode),
                ("state", "=", "assigned"),
            ]
            return model.search(source_document_domain)
        return model.browse()

    def _find_product(self, parse_results, btype="product"):
        model = self.env["product.product"]
        barcode = self._get_parse_results_value(parse_results, btype)
        if not barcode:
            return model.browse()
        return model.search(
            ["|", ("barcode", "=", barcode), ("default_code", "=", barcode)],
            limit=1,
        )

    def _find_lot(self, parse_results, btype="lot"):
        model = self.env["stock.lot"]
        barcode = self._get_parse_results_value(parse_results, btype)
        if not barcode:
            return model.browse()
        domain = [
            ("company_id", "=", self.env.company.id),
            ("name", "=", barcode),
        ]
        if self._products:
            domain.append(("product_id", "in", self._products.ids))
        return model.search(domain, limit=self._limit)

    def _find_packaging(self, parse_results, btype="packaging"):
        model = self.env["product.packaging"]
        barcode = self._get_parse_results_value(parse_results, btype)
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

    def _find_delivery_packaging(self, parse_results, btype="delivery_packaging"):
        model = self.env["stock.package.type"]
        barcode = self._get_parse_results_value(parse_results, btype)
        if not barcode:
            return model.browse()
        return model.search([("barcode", "=", barcode)], limit=1)

    def _find_origin_move(self, parse_results, btype="origin_move"):
        model = self.env["stock.move"]
        barcode = self._get_parse_results_value(parse_results, btype)
        outgoing_move_domain = [
            # We could have the same origin for multiple transfers
            # but we're interested only in the "done" ones.
            ("origin", "=", barcode),
            ("state", "=", "done"),
        ]
        if self._extra_domain:
            outgoing_move_domain = AND([outgoing_move_domain, self._extra_domain])
        return model.search(outgoing_move_domain)

    def dummy_from_scan(self, barcode):
        return None

    def _find_expiration_date(self, parse_results, btype="expiration_date"):
        # TODO
        return None
