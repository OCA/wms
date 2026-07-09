# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# Copyright 2024 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.osv.expression import AND

from odoo.addons.component.core import Component


class InvalidProduct(Exception):
    __slots__ = ("recordset", "type_")

    def __init__(self, recordset, type_):
        self.recordset = recordset
        self.type_ = type_


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

    def __init__(
        self,
        work_context,
        products=None,
        limit=1,
        use_origin=False,
        extra_domain=None,
    ):
        super().__init__(work_context)
        self._products = products
        self._limit = limit
        self._use_origin = use_origin
        self._extra_domain = extra_domain

    def _get_properties(self):
        return {
            "products": self._products,
            "limit": self._limit,
            "use_origin": self._use_origin,
            "extra_domain": self._extra_domain,
        }

    def _clone_with(self, **updates):
        """Helper to return a new instance with updated properties."""
        kwargs = self._get_properties()
        kwargs.update(updates)
        # Pass the existing work_context cleanly to the new instance
        return self.__class__(self.work, **kwargs)

    def for_products(self, products):
        return self._clone_with(products=products)

    def with_limit(self, limit):
        return self._clone_with(limit=limit)

    def with_origin(self, use_origin=True):
        return self._clone_with(use_origin=use_origin)

    def with_domain(self, extra_domain):
        return self._clone_with(extra_domain=extra_domain)

    @property
    def _barcode_type_handler(self):
        return {
            "product": self._find_product,
            "package": self._find_package,
            "picking": self._find_picking,
            "location": self._find_location,
            "lot": self._find_lot,
            "packaging": self._find_packaging,
            "delivery_packaging": self._find_delivery_packaging,
            "origin_move": self._find_origin_move,
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

    def find(self, barcode: str, types: list[str] = None):
        """Find Odoo record matching given `barcode`."""
        barcode = barcode or ""
        # TODO: decide the best default order in case we don't pass `types`
        types = types or self._barcode_type_handler.keys()

        parse_results = self.parser.parse(barcode)

        for btype in types:
            handler = self._barcode_type_handler.get(btype)
            if not handler:
                continue

            record = handler(parse_results, btype=btype)
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

    def location_from_scan(self, barcode, limit=1):
        res = self.with_limit(limit).find(barcode, types=["location"])
        return res.record if res else self.env["stock.location"].browse()

    def package_from_scan(self, barcode):
        res = self.find(barcode, types=["package"])
        return res.record if res else self.env["stock.quant.package"].browse()

    def picking_from_scan(self, barcode):
        res = self.find(barcode, types=["picking"])
        return res.record if res else self.env["stock.picking"].browse()

    def product_from_scan(self, barcode):
        res = self.find(barcode, types=["product"])
        return res.record if res else self.env["product.product"].browse()

    def lot_from_scan(self, barcode, products=None, limit=1):
        res = self.for_products(products).with_limit(limit).find(barcode, types=["lot"])
        return res.record if res else self.env["stock.lot"].browse()

    def packaging_from_scan(self, barcode):
        res = self.find(barcode, types=["packaging"])
        return res.record if res else self.env["product.packaging"].browse()

    def delivery_packaging_from_scan(self, barcode):
        res = self.find(barcode, types=["delivery_packaging"])
        return res.record if res else self.env["stock.package.type"].browse()

    def origin_move_from_scan(self, barcode):
        res = self.find(barcode, types=["origin_move"])
        return res.record if res else self.env["stock.move"].browse()

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
        return model.search([("name", "=", barcode)], limit=self._limit)

    def _find_picking(self, parse_results, btype="picking"):
        model = self.env["stock.picking"]
        barcode = self._get_parse_results_value(parse_results, btype)
        if not barcode:
            return model.browse()
        picking = model.search([("name", "=", barcode)], limit=self._limit)
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
            return model.search(source_document_domain, limit=self._limit)
        return model.browse()

    def _find_product(self, parse_results, btype="product"):
        model = self.env["product.product"]
        barcode = self._get_parse_results_value(parse_results, btype)
        if not barcode:
            return model.browse()
        products = model.search(
            ["|", ("barcode", "=", barcode), ("default_code", "=", barcode)],
            limit=self._limit,
        )
        if self._products and products:
            valid_products = products & self._products
            if not valid_products:
                raise InvalidProduct(products - self._products, "product")
            return valid_products
        return products

    def _find_lot(self, parse_results, btype="lot"):
        model = self.env["stock.lot"]
        barcode = self._get_parse_results_value(parse_results, btype)
        if not barcode:
            return model.browse()
        domain = [
            ("company_id", "=", self.env.company.id),
            ("name", "=", barcode),
        ]
        products = None
        if parse_results.get("product"):
            invalid_products = invalid_packagings = False
            try:
                products = self.with_limit(None)._find_product(parse_results)
            except InvalidProduct as e:
                invalid_products = e.recordset
            try:
                packagings = self.with_limit(None)._find_packaging(parse_results)
            except InvalidProduct as e:
                invalid_packagings = e.recordset

            if invalid_products and invalid_packagings:
                raise (
                    InvalidProduct(invalid_products, "product")
                    if invalid_products
                    else InvalidProduct(invalid_packagings, "packaging")
                )

            products |= packagings.product_id
            if not products:
                return model
            if self._products:
                products = products & self._products
            domain.append(("product_id", "in", products.ids))

        elif self._products:
            domain.append(("product_id", "in", self._products.ids))
        return model.search(domain, limit=self._limit)

    def _find_packaging(self, parse_results, btype="products"):
        model = self.env["product.packaging"]
        barcode = self._get_parse_results_value(parse_results, btype)
        if not barcode:
            return model.browse()
        packagings = model.search(
            [("barcode", "=", barcode), ("product_id", "!=", False)], limit=self._limit
        )
        if self._products and packagings:
            valid_packagings = packagings.filtered(
                lambda p: p.product_id in self._products
            )
            if not valid_packagings:
                raise InvalidProduct(packagings - valid_packagings, "packaging")
            return valid_packagings
        return packagings

    def _find_delivery_packaging(self, parse_results, btype="delivery_packaging"):
        model = self.env["stock.package.type"]
        barcode = self._get_parse_results_value(parse_results, btype)
        if not barcode:
            return model.browse()
        return model.search([("barcode", "=", barcode)], limit=self._limit)

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
        return model.search(outgoing_move_domain, limit=self._limit)
