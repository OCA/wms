# Copyright 2019-2021 Camptocamp SA
# Copyright 2019-2021 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
import logging

from psycopg2 import sql

from odoo import api, fields, models
from odoo.tools import float_compare

_logger = logging.getLogger(__name__)


class StockLocation(models.Model):

    _inherit = "stock.location"

    location_storage_type_ids = fields.Many2many(
        "stock.location.storage.type",
        "stock_location_location_storage_type_rel",
        "location_id",
        "location_storage_type_id",
        help="Location storage types defined here will be applied on all the "
        "children locations that do not define their own location "
        "storage types.",
    )
    allowed_location_storage_type_ids = fields.Many2many(
        "stock.location.storage.type",
        "stock_location_allowed_location_storage_type_rel",
        "location_id",
        "location_storage_type_id",
        compute="_compute_allowed_location_storage_type_ids",
        store=True,
        help="Locations storage types that this location can accept. (If no "
        "location storage types are defined on this specific location, "
        "the location storage types of the parent location are applied).",
    )
    pack_putaway_strategy = fields.Selection(
        selection=[
            ("none", "None"),
            ("ordered_locations", "Ordered Children Locations"),
        ],
        required=True,
        default="none",
        string="Packs Put-Away Strategy",
        help="This defines the storage strategy to use when packs are put "
        "away in this location.\n"
        "None: when a pack is moved to this location, it will not be put"
        " away any further.\n"
        "Ordered Children Locations: when a pack is moved to this "
        "location, a suitable location will be searched in its children "
        "locations according to the restrictions defined on their "
        "respective location storage types.",
    )
    pack_putaway_sequence = fields.Integer()
    storage_location_sequence_ids = fields.One2many(
        "stock.storage.location.sequence",
        "location_id",
        string="Storage locations sequences",
    )
    location_is_empty = fields.Boolean(
        compute="_compute_location_is_empty",
        store=True,
        help="technical field: True if the location is empty "
        "and there is no pending incoming products in the location. "
        " Computed only if the location needs to check for emptiness "
        '(has an "only empty" location storage type).',
    )

    in_move_ids = fields.One2many(
        "stock.move",
        "location_dest_id",
        domain=[
            ("state", "in", ("waiting", "confirmed", "partially_available", "assigned"))
        ],
        help="technical field: the pending incoming stock.moves in the location",
    )

    in_move_line_ids = fields.One2many(
        "stock.move.line",
        "location_dest_id",
        domain=[
            ("state", "in", ("waiting", "confirmed", "partially_available", "assigned"))
        ],
        help="technical field: the pending incoming "
        "stock.move.lines in the location",
    )
    out_move_line_ids = fields.One2many(
        "stock.move.line",
        "location_id",
        domain=[
            ("state", "in", ("waiting", "confirmed", "partially_available", "assigned"))
        ],
        help="technical field: the pending outgoing "
        "stock.move.lines in the location",
    )
    location_will_contain_lot_ids = fields.Many2many(
        "stock.production.lot",
        store=True,
        compute="_compute_location_will_contain_lot_ids",
        help="technical field: list of stock.production.lots in "
        "the location, either now or in pending operations",
    )
    location_will_contain_product_ids = fields.Many2many(
        "product.product",
        store=True,
        compute="_compute_location_will_contain_product_ids",
        help="technical field: list of products in "
        "the location, either now or in pending operations",
    )

    leaf_location_ids = fields.Many2many(
        "stock.location",
        compute="_compute_leaf_location_ids",
        help="technical field: all the leaves locations",
    )
    leaf_child_location_ids = fields.Many2many(
        "stock.location",
        compute="_compute_leaf_location_ids",
        help="technical field: all the leaves sub-locations",
    )
    max_height = fields.Float(
        string="Max height (mm)",
        compute="_compute_max_height",
        store=True,
        help="The max height supported among allowed location storage types.",
    )
    do_not_mix_products = fields.Boolean(
        compute="_compute_do_not_mix_products", store=True,
    )
    do_not_mix_lots = fields.Boolean(compute="_compute_do_not_mix_lots", store=True,)
    only_empty = fields.Boolean(compute="_compute_only_empty", store=True,)

    @api.depends(
        "usage",
        "allowed_location_storage_type_ids",
        "allowed_location_storage_type_ids.do_not_mix_products",
    )
    def _compute_do_not_mix_products(self):
        for rec in self:
            rec.do_not_mix_products = rec.usage == "internal" and any(
                storage_type.do_not_mix_products
                for storage_type in rec.allowed_location_storage_type_ids
            )

    @api.depends(
        "usage",
        "allowed_location_storage_type_ids",
        "allowed_location_storage_type_ids.do_not_mix_lots",
    )
    def _compute_do_not_mix_lots(self):
        for rec in self:
            rec.do_not_mix_lots = rec.usage == "internal" and any(
                storage_type.do_not_mix_lots
                for storage_type in rec.allowed_location_storage_type_ids
            )

    @api.depends(
        "usage",
        "allowed_location_storage_type_ids",
        "allowed_location_storage_type_ids.only_empty",
    )
    def _compute_only_empty(self):
        for rec in self:
            rec.only_empty = rec.usage == "internal" and any(
                storage_type.only_empty
                for storage_type in rec.allowed_location_storage_type_ids
            )

    @api.depends("child_ids.leaf_location_ids", "child_ids.active")
    def _compute_leaf_location_ids(self):
        """Compute all children leaf locations. Current location is excluded (not a child)"""
        query = """
            SELECT parent.id, ARRAY_AGG(sub.id) AS leaves
            FROM stock_location parent
            INNER JOIN stock_location sub
            ON sub.parent_path LIKE parent.parent_path || '%%'
            AND sub.id != parent.id
            AND sub.active
            LEFT JOIN stock_location subsub
            ON subsub.location_id = sub.id
            AND subsub.active
            WHERE
            -- exclude any location which has children so we keep only leaves
            subsub.id IS NULL
            AND parent.id in %s
            GROUP BY parent.id;
        """
        self.env.cr.execute(query, (tuple(self.ids),))
        rows = dict(self.env.cr.fetchall())
        for loc in self:
            leave_ids = rows.get(loc.id)
            if not leave_ids:
                loc.leaf_location_ids = loc
                loc.leaf_child_location_ids = False
                continue
            leaves = self.search([("id", "in", leave_ids)])
            loc.leaf_location_ids = leaves
            loc.leaf_child_location_ids = leaves

    def _should_compute_will_contain_product_ids(self):
        return self.do_not_mix_products

    def _should_compute_will_contain_lot_ids(self):
        return self.do_not_mix_lots

    def _should_compute_location_is_empty(self):
        return self.only_empty

    @api.depends(
        "quant_ids", "in_move_ids", "in_move_line_ids", "do_not_mix_products",
    )
    def _compute_location_will_contain_product_ids(self):
        for rec in self:
            if not rec._should_compute_will_contain_product_ids():
                if rec.location_will_contain_product_ids:
                    no_product = self.env["product.product"].browse()
                    rec.location_will_contain_product_ids = no_product
                continue
            products = (
                rec.mapped("quant_ids.product_id")
                | rec.mapped("in_move_ids.product_id")
                | rec.mapped("in_move_line_ids.product_id")
            )
            rec.location_will_contain_product_ids = products

    @api.depends(
        "quant_ids", "in_move_line_ids", "do_not_mix_lots",
    )
    def _compute_location_will_contain_lot_ids(self):
        for rec in self:
            if not rec._should_compute_will_contain_lot_ids():
                if rec.location_will_contain_lot_ids:
                    no_lot = self.env["stock.production.lot"].browse()
                    rec.location_will_contain_lot_ids = no_lot
                continue
            lots = rec.mapped("quant_ids.lot_id") | rec.mapped(
                "in_move_line_ids.lot_id"
            )
            rec.location_will_contain_lot_ids = lots

    @api.depends(
        "quant_ids.quantity",
        "out_move_line_ids.qty_done",
        "in_move_ids",
        "in_move_line_ids",
        "only_empty",
    )
    def _compute_location_is_empty(self):
        for rec in self:
            # No restriction should apply on customer/supplier/...
            # locations and we don't need to compute is empty
            # if there is no limit on the location
            if not rec._should_compute_location_is_empty():
                # avoid write if not required
                if not rec.location_is_empty:
                    rec.location_is_empty = True
                continue
            # we do want to keep a write here even if the value is the same
            # to enforce concurrent transaction safety: 2 moves taking
            # quantities in a location have to be executed sequentially
            # or the location could remain "not empty"
            if (
                sum(rec.quant_ids.mapped("quantity"))
                - sum(rec.out_move_line_ids.mapped("qty_done"))
                > 0
                or rec.in_move_ids
                or rec.in_move_line_ids
            ):
                rec.location_is_empty = False
            else:
                rec.location_is_empty = True

    @api.depends(
        "location_storage_type_ids",
        "location_id",
        "location_id.allowed_location_storage_type_ids",
    )
    def _compute_allowed_location_storage_type_ids(self):
        for location in self:
            if location.location_storage_type_ids:
                location.allowed_location_storage_type_ids = [
                    (6, 0, location.location_storage_type_ids.ids)
                ]
            else:
                parent = location.location_id
                location.allowed_location_storage_type_ids = [
                    (6, 0, parent.allowed_location_storage_type_ids.ids)
                ]

    @api.depends("allowed_location_storage_type_ids.max_height")
    def _compute_max_height(self):
        """Get the max height supported by location types, knowing that a max
        height of 0 means 'no limit', so it's considered as the maximum value.
        """
        for location in self:
            allowed_types = location.allowed_location_storage_type_ids
            types_with_max_height = allowed_types.filtered(
                lambda o: bool(o.max_height)
            ).sorted("max_height", reverse=True)
            types_without_max_height = allowed_types - types_with_max_height
            types_sorted = types_without_max_height + types_with_max_height
            location.max_height = (
                types_sorted.mapped("max_height")[0] if types_sorted else 0
            )

    # method provided by "stock_putaway_hook"
    def _putaway_strategy_finalizer(self, putaway_location, product):
        putaway_location = super()._putaway_strategy_finalizer(
            putaway_location, product
        )
        quant = self.env.context.get("storage_quant")
        return self._get_pack_putaway_strategy(putaway_location, quant, product)

    def _get_pack_putaway_strategy(self, putaway_location, quant, product):
        package_storage_type = False
        if quant:
            package_storage_type = quant.package_id.package_storage_type_id
            _logger.debug(
                "Computing putaway for pack %s (%s)"
                % (quant.package_id.name, quant.package_id)
            )
        # I'm not sure about this. I had to add the line, because there is a
        # second call to get_putaway_strategy which is made a 'leaf' location
        # as putaway_location which does not match the package storage type in
        # the project. This could be caused by another module, I'm not sure...
        if not package_storage_type:
            return putaway_location
        dest_location = putaway_location or self
        _logger.debug("putaway location: %s", dest_location.name)
        package_locations = self.env["stock.storage.location.sequence"].search(
            [
                ("package_storage_type_id", "=", package_storage_type.id),
                ("location_id", "child_of", dest_location.ids),
            ]
        )
        if not package_locations:
            return dest_location

        for package_sequence in package_locations:
            pref_loc = package_sequence.location_id
            if (
                pref_loc.pack_putaway_strategy == "none"
                and pref_loc.select_allowed_locations(
                    package_storage_type, quant, product
                )
            ):
                _logger.debug(
                    "No putaway strategy defined on location %s and package "
                    "storage type %s allowed."
                    % (pref_loc.complete_name, package_storage_type.name)
                )
                return pref_loc
            storage_locations = pref_loc.get_storage_locations(products=product)
            _logger.debug("Storage locations selected: %s" % storage_locations)
            allowed_location = storage_locations.select_first_allowed_location(
                package_storage_type, quant, product
            )
            if allowed_location:
                _logger.debug(
                    "Applied putaway strategy to location %s"
                    % allowed_location.complete_name
                )
                return allowed_location
        _logger.debug(
            "Could not find a valid putaway location, fallback to %s"
            % putaway_location.complete_name
        )
        return putaway_location

    def get_storage_locations(self, products=None):
        # TODO support multiple products? cf ABC
        self.ensure_one()
        locations = self.browse()
        if self.pack_putaway_strategy == "none":
            locations = self
        else:
            products = products or self.env["product.product"]
            locations = self._get_sorted_leaf_child_locations(products)
        return locations

    def _get_sorted_leaf_locations_orderby(self, products):
        """Return SQL orderby clause and params for sorting locations

        First, locations are ordered by max height, knowing that a max height of 0
        means "no limit" and as such it should be among the last locations.
        Then, they are ordered by a sequence and name.
        """
        self.env["stock.location"].flush(
            ["max_height", "pack_putaway_sequence", "name"]
        )
        orderby = []
        if self.pack_putaway_strategy == "ordered_locations":
            orderby = [
                "CASE WHEN max_height > 0 THEN max_height ELSE 'Infinity' END",
                "pack_putaway_sequence",
                "name",
                "id",
            ]
        return ", ".join(orderby), []

    def _get_sorted_leaf_child_locations(self, products):
        """Return sorted leaf sub-locations

        The locations are candidate locations that will be evaluated one per
        one in order to find the first available location. They must be leaf
        locations where we can actually put goods.
        """
        if not self.leaf_child_location_ids:
            return self.leaf_child_location_ids
        query = self._where_calc([("id", "in", self.leaf_child_location_ids.ids)])
        from_clause, where_clause, where_params = query.get_sql()
        orderby_clause, orderby_params = self._get_sorted_leaf_locations_orderby(
            products
        )
        query = sql.SQL(
            "SELECT id FROM {table} WHERE {where} ORDER BY {orderby}"
        ).format(
            table=sql.Identifier(self._table),
            where=sql.SQL(where_clause),
            orderby=sql.SQL(orderby_clause),
        )
        self._cr.execute(query, where_params + orderby_params)
        location_ids = [x[0] for x in self.env.cr.fetchall()]
        return self.env["stock.location"].browse(location_ids)

    def select_first_allowed_location(self, package_storage_type, quants, products):
        allowed = self.select_allowed_locations(
            package_storage_type, quants, products, limit=1
        )
        return allowed

    def _domain_location_storage_type_constraints(
        self, package_storage_type, quants, products
    ):
        """Compute the domain for the location storage type which match the package
        storage type

        This method also checks the "capacity" constraints (height and weight)
        """
        # There can be multiple location storage types for a given
        # location, so we need to filter on the ones relative to the package
        # we consider.
        LocStorageType = self.env["stock.location.storage.type"]
        compatible_location_storage_types = LocStorageType.search(
            [("location_ids", "in", self.ids)]
        )

        pertinent_loc_storagetype_domain = [
            ("id", "in", compatible_location_storage_types.ids),
            ("package_storage_type_ids", "=", package_storage_type.id),
        ]
        if quants.package_id.height:
            pertinent_loc_storagetype_domain += [
                "|",
                ("max_height", "=", 0),
                ("max_height", ">=", quants.package_id.height),
            ]
        package_weight = (
            quants.package_id.pack_weight or quants.package_id.estimated_pack_weight
        )
        if package_weight:
            pertinent_loc_storagetype_domain += [
                "|",
                ("max_weight", "=", 0),
                ("max_weight", ">=", package_weight),
            ]
        _logger.debug(
            "pertinent storage type domain: %s", pertinent_loc_storagetype_domain
        )
        return pertinent_loc_storagetype_domain

    def _allowed_locations_for_location_storage_types(
        self, location_storage_types, quants, products
    ):
        valid_location_ids = set()
        for loc_storage_type in location_storage_types:
            location_domain = loc_storage_type._domain_location_storage_type(
                self, quants, products
            )
            _logger.debug("pertinent location domain: %s", location_domain)
            locations = self.search(location_domain)
            valid_location_ids |= set(locations.ids)
        return self.browse(valid_location_ids)

    def _select_final_valid_putaway_locations(self, limit=None):
        """Return the valid locations using the provided limit

        ``self`` contains locations already ordered and contains
        only valid locations.
        This method can be used as a hook to add or remove valid
        locations based on other properties. Pay attention to
        keep the order.
        """
        return self[:limit]

    def select_allowed_locations(
        self, package_storage_type, quants, products, limit=None
    ):
        """Filter allowed locations for a storage type

        ``self`` contains locations already ordered according to the
        putaway strategy, so beware of the return that must keep the
        same order
        """
        # We have package who may be placed in a stock.location
        #
        # 1. On the stock.location there are location_storage_type and on the
        # packages there are package_storage_type. Between both, there's a m2m
        # who says which package ST can be placed in which location ST
        #
        # 2. On a location_ST there are some additional restrictions: a -
        # capacity (volume / height / weight) and b - properties (boolean
        # flags: only empty, don't mix lots, don't mix products)
        LocStorageType = self.env["stock.location.storage.type"]
        _logger.debug(
            "select allowed location for package storage type %s (q=%s, p=%s)",
            package_storage_type.name,
            quants,
            products.mapped("name"),
        )
        # 1: filter locations on compatible storage type
        compatible_locations = self.search(
            [
                ("id", "in", self.ids),
                (
                    "allowed_location_storage_type_ids",
                    "in",
                    package_storage_type.location_storage_type_ids.ids,
                ),
            ]
        )
        pertinent_loc_s_t_domain = compatible_locations._domain_location_storage_type_constraints(  # noqa
            package_storage_type, quants, products
        )

        pertinent_loc_storage_types = LocStorageType.search(pertinent_loc_s_t_domain)

        # now loop over the pertinent location storage types (there should be
        # few of them) and check for properties to find suitable locations
        valid_locations = compatible_locations._allowed_locations_for_location_storage_types(  # noqa
            pertinent_loc_storage_types, quants, products
        )

        valid_locations = self._order_allowed_locations(valid_locations)
        valid_locations = valid_locations._select_final_valid_putaway_locations(
            limit=limit
        )

        _logger.debug(
            "select allowed location for package storage"
            " type %s (q=%s, p=%s) found %d locations",
            package_storage_type.name,
            quants,
            products.mapped("name"),
            len(valid_locations),
        )
        return valid_locations

    def _order_allowed_locations(self, valid_locations):
        """Return the ordered list of valid_locations

        By default the order should be the same as self. However, if the
        valid_locations list contains locations configured to not mix products,
        we must give priority to locations that already contains products
        (the ones with less qty first)
        """
        valid_no_mix = valid_locations.filtered("do_not_mix_products")
        loc_ordered_by_qty = []
        if valid_no_mix:
            StockQuant = self.env["stock.quant"]
            domain_quant = [("location_id", "in", valid_no_mix.ids)]
            loc_ordered_by_qty = [
                item["location_id"][0]
                for item in StockQuant.read_group(
                    domain_quant,
                    ["location_id", "quantity"],
                    ["location_id"],
                    orderby="quantity",
                )
                if (float_compare(item["quantity"], 0, precision_digits=2) > 0)
            ]
        valid_location_ids = set(valid_locations.ids) - set(loc_ordered_by_qty)
        ordered_valid_location_ids = loc_ordered_by_qty + [
            id_ for id_ in self.ids if id_ in valid_location_ids
        ]
        valid_locations = self.browse(ordered_valid_location_ids)
        return valid_locations
