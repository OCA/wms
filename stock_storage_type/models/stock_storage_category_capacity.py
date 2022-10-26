# Copyright 2022 ACSONE SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class StorageCategoryProductCapacity(models.Model):

    _inherit = "stock.storage.category.capacity"

    allow_new_product = fields.Selection(
        [
            ("empty", "If the location is empty"),
            ("same", "If all products are same"),
            ("mixed", "Allow mixed products"),
        ],
        default="mixed",
        required=True,
    )
    do_not_mix_lots = fields.Boolean(
        compute="_compute_do_not_mix_lots",
        readonly=False,
        store=True,
        help="If checked, moves to the destination location will only be "
        "allowed if the location contains product of the same "
        "lot.",
    )
    computed_location_ids = fields.One2many(
        comodel_name="stock.location",
        related="storage_category_id.computed_location_ids",
    )
    has_restrictions = fields.Boolean(
        compute="_compute_has_restrictions",
        help="Technical: This is used to check if we need to display warning message",
    )
    # TODO: Check if this is convenient with the constraint on barcode field
    # in core module
    active = fields.Boolean(default=True)

    @api.depends(
        "allow_new_product",
        "do_not_mix_lots",
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
                    capacity.do_not_mix_lots,
                    capacity.allow_new_product != "mixed",
                    capacity.storage_category_id.max_height,
                    capacity.storage_category_id.max_weight,
                ]
            )

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
        # TODO this method and domain is applied once per storage type. If it's
        # too slow at some point, we could group the storage types by similar
        # configuration (only_empty, do_not_mix_products, do_not_mix_lots) and
        # do a single query per set of options
        if self.allow_new_product == "empty":
            location_domain.append(("location_is_empty", "=", True))
        if self.allow_new_product == "same":
            location_domain += [
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
        if self.do_not_mix_lots:
            lots = quants.mapped("lot_id")
            location_domain += [
                "|",
                # same comment as for the products
                ("location_will_contain_lot_ids", "in", lots.ids),
                ("location_will_contain_lot_ids", "=", False),
            ]
        return location_domain

    @api.constrains(
        "allow_new_product",
        "do_not_mix_lots",
    )
    def _check_empty_mix(self):
        """
        Check if capacity 'do not mix lots' constraint is not set along with
        'empty' one.
        """
        for location_storage_type in self:
            if location_storage_type.allow_new_product == "empty" and (
                location_storage_type.do_not_mix_lots
                or location_storage_type.allow_new_product == "same"
            ):
                raise ValidationError(
                    _(
                        "You cannot set 'Do not mix lots' or 'Do not mix products'"
                        " with 'Only empty' constraint."
                    )
                )

    @api.constrains("do_not_mix_lots", "allow_new_product")
    def _check_do_not_mix(self):
        """
        Check if capacity 'do not mix lots' constraint is set along with
        'same product' one.
        """
        for capacity in self:
            if capacity.do_not_mix_lots and not capacity.allow_new_product == "same":
                raise ValidationError(
                    _(
                        "You cannot set 'Do not mix lots' without setting "
                        "'Allow New Product' to 'If all products are same' constraint."
                    )
                )

    @api.depends("allow_new_product")
    def _compute_do_not_mix_lots(self):
        """
        The value of this field can be set manually.
        This changes it only if allow_new_product == "same
        """
        capacities_to_update = self.filtered(
            lambda capacity: capacity.allow_new_product == "same"
            and capacity.do_not_mix_lots
        )
        capacities_to_update.update({"do_not_mix_lots": False})
