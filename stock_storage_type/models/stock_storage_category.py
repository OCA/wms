# Copyright 2022 ACSONE SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import api, fields, models


class StockStorageCategory(models.Model):

    _inherit = "stock.storage.category"

    allow_new_product = fields.Selection(
        selection_add=[("same_lot", "If lots are all the same")],
        ondelete={"same_lot": "cascade"},
    )

    computed_location_ids = fields.One2many(
        comodel_name="stock.location", inverse_name="computed_storage_category_id"
    )
    allow_new_product_ids = fields.One2many(
        comodel_name="stock.storage.category.allow_new_product",
        inverse_name="storage_category_id",
        string="Allow New Product Rules",
    )

    # TODO: Move these fields in another module ?
    max_height = fields.Float(
        string="Max height (mm)",
        help="The max height supported for this storage category.",
    )

    max_height_in_m = fields.Float(
        help="Technical field, to speed up comparaisons",
        compute="_compute_max_height_in_m",
        store=True,
    )
    weight_uom_id = fields.Many2one(
        # Same as product.packing
        "uom.uom",
        string="Weight Units of Measure",
        domain=lambda self: [
            ("category_id", "=", self.env.ref("uom.product_uom_categ_kgm").id)
        ],
        help="Weight Unit of Measure",
        compute=False,
        default=lambda self: self.env[
            "product.template"
        ]._get_weight_uom_id_from_ir_config_parameter(),
    )
    weight_uom_name = fields.Char(
        # Same as product.packing
        string="Weight unit of measure label",
        related="weight_uom_id.name",
        readonly=True,
    )
    max_weight_in_kg = fields.Float(
        help="Technical field, to speed up comparaisons",
        compute="_compute_max_weight_in_kg",
        store=True,
    )
    length_uom_id = fields.Many2one(
        # Same as product.packing
        "uom.uom",
        "Dimensions Units of Measure",
        domain=lambda self: [
            ("category_id", "=", self.env.ref("uom.uom_categ_length").id)
        ],
        help="UoM for height",
        default=lambda self: self.env[
            "product.template"
        ]._get_length_uom_id_from_ir_config_parameter(),
    )
    has_restrictions = fields.Boolean(
        compute="_compute_has_restrictions",
        help="Technical: This is used to check if we need to display warning message",
    )

    _sql_constraints = [
        (
            "positive_max_height",
            "CHECK(max_height >= 0)",
            "Max height should be a positive number.",
        ),
    ]

    @api.depends("max_height", "length_uom_id")
    def _compute_max_height_in_m(self):
        uom_m = self.env.ref("uom.product_uom_meter")
        for slst in self:
            slst.max_height_in_m = slst.length_uom_id._compute_quantity(
                qty=slst.max_height,
                to_unit=uom_m,
                round=False,
            )

    @api.depends("max_weight")
    def _compute_max_weight_in_kg(self):
        uom_kg = self.env.ref("uom.product_uom_kgm")
        for slst in self:
            slst.max_weight_in_kg = slst.weight_uom_id._compute_quantity(
                qty=slst.max_weight,
                to_unit=uom_kg,
                round=False,
            )

    @api.depends(
        "allow_new_product",
        "allow_new_product_ids.allow_new_product",
        "max_height",
        "max_weight",
    )
    def _compute_has_restrictions(self):
        """
        A storage category has restrictions when it:
            - does not accept mixed products
            - or does not accept mixed lots
            - or do have a maximum height set on its category
            - or do have a maximum weight set on its category
        """
        for rec in self:
            rec.has_restrictions = any(
                [
                    rec.allow_new_product != "mixed",
                    any(
                        rule.allow_new_product != "mixed"
                        for rule in rec.allow_new_product_ids
                    ),
                    rec.max_height,
                    rec.max_weight,
                ]
            )

    def _get_product_location_domain(self, products):
        """
        Helper to get products location domain
        """
        return [
            "|",
            # Ideally, we would like a domain which is a strict comparison:
            # if we do not mix products, we should be able to filter on ==
            # product.id. Here, if we can create a move for product B and
            # set it's destination in a location already used by product A,
            # then all the new moves for product B will be allowed in the
            # location.
            ("location_will_contain_product_ids", "in", products.ids),
            ("location_will_contain_product_ids", "=", False),
        ]

    def _domain_location_storage_category(
        self, candidate_locations, quants, products, package_type
    ):
        """
        Compute a domain which applies the constraint of the
        Stock Storage Category to select locations among candidate locations.
        """
        self.ensure_one()
        location_domain = [
            ("id", "in", candidate_locations.ids),
            ("computed_storage_category_id", "in", self.ids),
        ]
        # Build the domain using the 'allow_new_product' field
        allow_new_product = self.get_allow_new_product(
            product=products,
            package_type=package_type,
            package=quants.package_id,
            quants=quants,
        )
        if allow_new_product == "empty":
            location_domain.append(("location_is_empty", "=", True))
        elif allow_new_product == "same":
            location_domain += self._get_product_location_domain(products)
        elif allow_new_product == "same_lot":
            lots = quants.mapped("lot_id")
            # As same lot should filter also on same product
            location_domain += self._get_product_location_domain(products)
            location_domain += [
                "|",
                # same comment as for the products
                ("location_will_contain_lot_ids", "in", lots.ids),
                ("location_will_contain_lot_ids", "=", False),
            ]
        return location_domain

    def get_allow_new_product(
        self,
        product,
        package_type=None,
        package=None,
        quants=None,
    ):
        """Return the `allow_new_product` option value.

        It first evaluates the conditions based on different criteria, and if no
        value can be found among them it fallbacks on the category option value.
        """
        self.ensure_one()
        for rule in self.allow_new_product_ids:
            res = True
            for condition in rule.condition_ids:
                res = condition.evaluate(
                    self,
                    product,
                    package_type,
                    package,
                    quants,
                )
                if not res:
                    # Go to next rule
                    break
            # All conditions are matching
            if res:
                return rule.allow_new_product
        # Fallback on category option value
        return self.allow_new_product
