# Copyright 2022 ACSONE SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import _, api, fields, models


class StorageCategoryProductCapacity(models.Model):

    _inherit = "stock.storage.category.capacity"

    allow_new_product = fields.Selection(
        selection=[
            ("empty", "If the location is empty"),
            ("same", "If all products are same"),
            ("mixed", "Allow mixed products"),
            ("same_lot", "If all lots are the same"),
        ],
        default="mixed",
        required=True,
    )
    computed_location_ids = fields.One2many(
        comodel_name="stock.location",
        related="storage_category_id.computed_location_ids",
    )
    has_restrictions = fields.Boolean(
        compute="_compute_has_restrictions",
        help="Technical: This is used to check if we need to display warning message",
    )

    @api.model
    def _get_display_name_attributes(self):
        """
        Adds the storage capacity attributes to compose the display name
        """
        attributes = super()._get_display_name_attributes()
        value = self._fields["allow_new_product"].convert_to_export(
            self.allow_new_product, self
        )
        attributes.append(_("Allow New Product: ") + value)
        return attributes

    @api.model
    def _compute_display_name_depends(self):
        depends = super()._compute_display_name_depends()
        depends.append("allow_new_product")
        return depends

    @api.depends(
        "allow_new_product",
        "storage_category_id.max_height",
        "storage_category_id.max_weight",
    )
    def _compute_has_restrictions(self):
        """
        A storage capacity has restrictions when it:
            - does not accept mixed products
            - or does not accept mixed lots
            - or do have a maximum height set on its category
            - or do have a maximum weight set on its category
        """
        for capacity in self:
            capacity.has_restrictions = any(
                [
                    capacity.allow_new_product != "mixed",
                    capacity.storage_category_id.max_height,
                    capacity.storage_category_id.max_weight,
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

    def _domain_location_storage_type(self, candidate_locations, quants, products):
        """
        Compute a domain which applies the constraint of the
        Stock Storage Category Capacities to select locations among candidate
        locations.
        """
        self.ensure_one()
        location_domain = [
            ("id", "in", candidate_locations.ids),
            ("computed_storage_category_id.capacity_ids", "in", self.ids),
        ]
        # Build the domain using the 'allow_new_product' field
        if self.allow_new_product == "empty":
            location_domain.append(("location_is_empty", "=", True))
        elif self.allow_new_product == "same":
            location_domain += self._get_product_location_domain(products)
        elif self.allow_new_product == "same_lot":
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
