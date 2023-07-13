# Copyright 2019-2021 Camptocamp SA
# Copyright 2019-2021 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
import logging

from psycopg2 import sql

from odoo import api, fields, models
from odoo.fields import Command
from odoo.tools import float_compare

_logger = logging.getLogger(__name__)


class StockLocation(models.Model):

    _inherit = "stock.location"

    computed_storage_category_id = fields.Many2one(
        comodel_name="stock.storage.category",
        string="Computed Storage Category",
        compute="_compute_computed_storage_category_id",
        store=True,
        recursive=True,
        help="This represents the Storage Category that will be used. It depends either "
        "on the category set on the location or on one of its parent.",
    )
    computed_storage_capacity_ids = fields.One2many(
        related="computed_storage_category_id.capacity_ids",
    )
    pack_putaway_strategy = fields.Selection(
        selection=[
            ("none", "None"),
            ("ordered_locations", "Ordered Children Locations"),
        ],
        required=True,
        default="none",
        string="Put-Away Strategy",
        help="This defines the storage strategy based on package type to use when "
        "a product or package is put away in this location.\n"
        "None: when moved to this location, it will not be put"
        " away any further.\n"
        "Ordered Children Locations: when moved to this "
        "location, a suitable location will be searched in its children "
        "locations according to the restrictions defined on their "
        "respective location storage types.",
    )
    package_type_putaway_sequence = fields.Integer(
        string="Putaway Sequence",
        help="Allow to sort the valid locations by sequence for the storage "
        "strategy based on package type",
    )
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
        recursive=True,
    )
    # TODO: Maybe renaming these fields as there are already such fields
    # in core but without domains. Something like 'pending_in_move_ids'
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
        "stock.lot",
        store=True,
        compute="_compute_location_will_contain_lot_ids",
        help="technical field: list of stock.lots in "
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
        recursive=True,
        help="technical field: all the leaves locations",
    )
    leaf_child_location_ids = fields.Many2many(
        "stock.location",
        compute="_compute_leaf_location_ids",
        recursive=True,
        help="technical field: all the leaves sub-locations",
    )
    max_height = fields.Float(
        related="computed_storage_category_id.max_height",
        store=True,
        recursive=True,
    )
    max_height_in_m = fields.Float(
        related="computed_storage_category_id.max_height_in_m",
        store=True,
        recursive=True,
    )

    do_not_mix_products = fields.Boolean(
        compute="_compute_do_not_mix_products", store=True, recursive=True
    )
    do_not_mix_lots = fields.Boolean(
        compute="_compute_do_not_mix_lots", store=True, recursive=True
    )
    only_empty = fields.Boolean(
        compute="_compute_only_empty", store=True, recursive=True
    )

    @api.depends(
        "usage",
        "computed_storage_category_id.allow_new_product",
        "computed_storage_category_id.capacity_ids.allow_new_product",
    )
    def _compute_do_not_mix_lots(self):
        """
        This computes the value that says if the location cannot have mixed lots from:
           - its own Storage Category value
           - one of its Storage Capacities value
        """
        for rec in self:
            rec.do_not_mix_lots = rec.usage == "internal" and (
                any(
                    storage_type.allow_new_product == "same_lot"
                    for storage_type in rec.computed_storage_category_id.capacity_ids
                )
                or rec.computed_storage_category_id.allow_new_product == "same_lot"
            )

    @api.depends(
        "usage",
        "computed_storage_category_id.allow_new_product",
        "computed_storage_category_id.capacity_ids.allow_new_product",
    )
    def _compute_only_empty(self):
        """
        This computes the value that says if the location cannot have mixed lots from:
           - its own Storage Category value
           - one of its Storage Capacities value
        """
        for rec in self:
            rec.only_empty = rec.usage == "internal" and (
                any(
                    storage_type.allow_new_product == "empty"
                    for storage_type in rec.computed_storage_category_id.capacity_ids
                )
                or rec.computed_storage_category_id.allow_new_product == "empty"
            )

    @api.depends(
        "usage",
        "computed_storage_category_id.allow_new_product",
        "computed_storage_category_id.capacity_ids.allow_new_product",
    )
    def _compute_do_not_mix_products(self):
        """
        This computes the value that says if the location cannot have mixed lots from:
           - its own Storage Category value
           - one of its Storage Capacities value
        """
        for rec in self:
            rec.do_not_mix_products = rec.usage == "internal" and (
                any(
                    storage_type.allow_new_product in ("same", "same_lot")
                    for storage_type in rec.computed_storage_category_id.capacity_ids
                )
                or rec.computed_storage_category_id.allow_new_product
                in ("same", "same_lot")
            )

    @api.depends(
        "location_id", "storage_category_id", "location_id.computed_storage_category_id"
    )
    def _compute_computed_storage_category_id(self):
        """
        This computes the Storage Category depending on:
          - its own Storage Category
          - or one of its parent (along the parent path) Storage Category
        """
        for location in self:
            if location.storage_category_id:
                location.computed_storage_category_id = location.storage_category_id
            else:
                parent = location.location_id
                location.computed_storage_category_id = parent.storage_category_id

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
        "quant_ids",
        "in_move_ids",
        "in_move_line_ids",
        "do_not_mix_products",
    )
    def _compute_location_will_contain_product_ids(self):
        for rec in self:
            if not rec._should_compute_will_contain_product_ids():
                no_product = self.env["product.product"].browse()
                rec.location_will_contain_product_ids = no_product
            else:
                products = (
                    rec.mapped("quant_ids.product_id")
                    | rec.mapped("in_move_ids.product_id")
                    | rec.mapped("in_move_line_ids.product_id")
                )
                rec.location_will_contain_product_ids = products

    @api.depends(
        "quant_ids",
        "in_move_line_ids",
        "do_not_mix_lots",
    )
    def _compute_location_will_contain_lot_ids(self):
        for rec in self:
            if not rec._should_compute_will_contain_lot_ids():
                no_lot = self.env["stock.lot"].browse()
                rec.location_will_contain_lot_ids = no_lot
            else:
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

    # method provided by "stock_putaway_hook"
    def _putaway_strategy_finalizer(
        self,
        putaway_location,
        product,
        quantity=0,
        package=None,
        packaging=None,
        additional_qty=None,
    ):
        putaway_location = super()._putaway_strategy_finalizer(
            putaway_location, product, quantity, package, packaging, additional_qty
        )
        if package:
            # If package provided, the product is not set (in the get_putaway_strategy() method)
            product = package.single_product_id or product
        return self._get_package_type_putaway_strategy(
            putaway_location, package, product, quantity
        )

    def _get_package_type(self, package, product):
        # Returns the package type either from the package, either from the product
        package_type = self.env["stock.package.type"].browse()
        if package:
            package_type = package.package_type_id
            _logger.debug(
                "Computing putaway for package %s of package type %s"
                % (package, package_type)
            )
        elif product.package_type_id:
            # Get default package type on product if defined
            package_type = product.package_type_id
            _logger.debug(
                "Computing putaway for product %s of package type %s"
                % (product, product.package_type_id)
            )
        return package_type

    def _get_package_type_putaway_strategy(
        self, putaway_location, package, product, quantity
    ):
        package_type = self._get_package_type(package, product)
        # exclude_sml_ids are passed into the context during the get_putaway_strategy
        # call.
        stock_move_line_ids = self.env.context.get("exclude_sml_ids", [])
        stock_move_lines = self.env["stock.move.line"].browse(stock_move_line_ids)
        quants = (
            package.quant_ids
            if package
            else stock_move_lines.mapped("reserved_quant_id")
        )
        if not package_type:
            # Fallback on standard one
            return putaway_location
        # TODO: Remove this and use only putaway_location as always filled in
        dest_location = putaway_location or self
        _logger.debug("putaway location: %s", dest_location.name)
        package_locations = self.env["stock.storage.location.sequence"].search(
            [
                ("package_type_id", "=", package_type.id),
                ("location_id", "child_of", dest_location.ids),
            ]
        )
        if not package_locations:
            return dest_location

        for package_sequence in package_locations:
            if not package_sequence.can_be_applied(putaway_location, quants, product):
                continue
            pref_loc = package_sequence.location_id
            storage_locations = pref_loc.get_storage_locations(products=product)
            _logger.debug("Storage locations selected: %s" % storage_locations)
            allowed_location = storage_locations.select_first_allowed_location(
                package_type, quants, product
            )
            if allowed_location:
                _logger.debug(
                    "Applied putaway strategy to location %s"
                    % allowed_location.complete_name
                )
                # Reapply putaway strategy if particular rules have been put on product level
                # Check if the allowed location is not self to avoid recursive computations
                if allowed_location != self:
                    final_location = allowed_location._get_putaway_strategy(
                        product, quantity, package
                    )
                    return final_location
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
            return locations
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
        self.env["stock.location"].flush_model(
            ["max_height", "package_type_putaway_sequence", "name"]
        )
        orderby = []
        if self.pack_putaway_strategy == "ordered_locations":
            orderby = [
                "CASE WHEN max_height > 0 THEN max_height ELSE 'Infinity' END",
                "package_type_putaway_sequence",
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
        _, where_clause, where_params = query.get_sql()
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

    def select_first_allowed_location(self, package_type, quants, products):
        allowed = self.select_allowed_locations(package_type, quants, products, limit=1)
        return allowed

    def _domain_location_storage_type_constraints(self, package_type, quants, products):
        """Compute the domain for the location storage type which match the package
        storage type

        This method also checks the "capacity" constraints (height and weight)
        """
        # There can be multiple location storage types for a given
        # location, so we need to filter on the ones relative to the package
        # we consider.
        Capacity = self.env["stock.storage.category.capacity"]
        compatible_location_storage_types = Capacity.search(
            [("computed_location_ids", "in", self.ids)]
        )

        pertinent_loc_storagetype_domain = [
            ("id", "in", compatible_location_storage_types.ids),
            ("package_type_id", "=", package_type.id),
        ]
        if quants.package_id.height:
            pertinent_loc_storagetype_domain += [
                "|",
                ("storage_category_id.max_height_in_m", "=", 0),
                (
                    "storage_category_id.max_height_in_m",
                    ">=",
                    quants.package_id.height_in_m,
                ),
            ]
        package_weight_kg = (
            quants.package_id.pack_weight_in_kg
            or quants.package_id.estimated_pack_weight_kg
        )
        if package_weight_kg:
            pertinent_loc_storagetype_domain += [
                "|",
                ("storage_category_id.max_weight_in_kg", "=", 0),
                ("storage_category_id.max_weight_in_kg", ">=", package_weight_kg),
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

    def select_allowed_locations(self, package_type, quants, products, limit=None):
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
        Capacity = self.env["stock.storage.category.capacity"]
        _logger.debug(
            "select allowed location for package storage type %s (q=%s, p=%s)",
            package_type.name,
            quants,
            products.mapped("name"),
        )
        # 1: filter locations on compatible storage type
        compatible_locations = self.search(
            [
                ("id", "in", self.ids),
                (
                    "computed_storage_category_id.capacity_ids",
                    "in",
                    package_type.storage_category_capacity_ids.ids,
                ),
            ]
        )
        pertinent_loc_s_t_domain = (
            compatible_locations._domain_location_storage_type_constraints(
                package_type, quants, products
            )
        )

        pertinent_loc_storage_types = Capacity.search(pertinent_loc_s_t_domain)

        # now loop over the pertinent location storage types (there should be
        # few of them) and check for properties to find suitable locations
        valid_locations = (
            compatible_locations._allowed_locations_for_location_storage_types(
                pertinent_loc_storage_types, quants, products
            )
        )

        valid_locations = self._order_allowed_locations(valid_locations)
        valid_locations = valid_locations._select_final_valid_putaway_locations(
            limit=limit
        )

        _logger.debug(
            "select allowed location for package storage"
            " type %s (q=%s, p=%s) found %d locations",
            package_type.name,
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

    @api.depends_context("fixed_child_internal_location")
    def _compute_child_internal_location_ids(self):
        """
        This will override the child selection by setting self as
        the only child.

        TODO: Maybe adding a field on view location in order to compute this
        without context changing
        """
        if self.env.context.get("fixed_child_internal_location"):
            internal_location_id = self.env.context.get("fixed_child_internal_location")
            internal_location = self.browse(internal_location_id)
            if internal_location_id:
                self.update(
                    {
                        "child_internal_location_ids": [
                            Command.set(internal_location.ids)
                        ]
                    }
                )
        else:
            return super()._compute_child_internal_location_ids()

    def _get_stock_storage_type_putaway_rules(
        self, product, package=None, packaging=None
    ):
        """
        We have retrieved the code from stock module in order to get
        the evaluated putaway rules on this location in order to determine
        if we should return self or super().
        """
        self = self._check_access_putaway()
        products = self.env.context.get("products", self.env["product.product"])
        products |= product
        # find package type on package or packaging
        package_type = self.env["stock.package.type"]
        if package:
            package_type = package.package_type_id
        elif packaging:
            package_type = packaging.package_type_id

        categ = (
            products.categ_id
            if len(products.categ_id) == 1
            else self.env["product.category"]
        )
        categs = categ
        while categ.parent_id:
            categ = categ.parent_id
            categs |= categ

        putaway_rules = self.putaway_rule_ids.filtered(
            lambda rule: (not rule.product_id or rule.product_id in products)
            and (not rule.category_id or rule.category_id in categs)
            and (not rule.package_type_ids or package_type in rule.package_type_ids)
        )
        return putaway_rules

    def _get_putaway_strategy(
        self, product, quantity=0, package=None, packaging=None, additional_qty=None
    ):
        """
        As standard Odoo method will return the first real child of a view,
        this is not convenient as if a storage sequence is set on that view,
        it won't be applied.

        So, we check if no putaway rule is set on the view, then set the id of
        the view to context to bypass the child_internal_location_ids field.
        """
        if self.usage == "view":
            putaway_rules = self._get_stock_storage_type_putaway_rules(
                product=product, package=package, packaging=packaging
            )
            if not putaway_rules:
                self_fixed_child = self.with_context(
                    fixed_child_internal_location=self.id
                )
                return super(StockLocation, self_fixed_child)._get_putaway_strategy(
                    product,
                    quantity=quantity,
                    package=package,
                    packaging=packaging,
                    additional_qty=additional_qty,
                )
        return super()._get_putaway_strategy(
            product,
            quantity=quantity,
            package=package,
            packaging=packaging,
            additional_qty=additional_qty,
        )
