# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.osv.expression import AND, OR


class StockLocation(models.Model):

    _inherit = "stock.location"

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
    storage_location_sequence_ids = fields.One2many(
        "stock.storage.location.sequence",
        "location_id",
        string="Storage locations sequences",
    )

    @api.constrains("pack_putaway_strategy", "storage_location_sequence_ids")
    def _check_pack_putaway_strategy(self):
        for location in self:
            if (
                location.pack_putaway_strategy == "none"
                and location.storage_location_sequence_ids
            ):
                raise ValidationError(
                    _(
                        "Changing Packs storage strategy to 'None' is not "
                        "allowed as the location %s is used in a Storage "
                        "locations for package storage type."
                    )
                    % location.name
                )

    def _get_putaway_strategy(self, product):
        putaway_location = super()._get_putaway_strategy(product)
        quant = self.env.context.get("storage_quant")
        return self._get_pack_putaway_strategy(
            putaway_location, quant, product
        )

    def _get_pack_putaway_strategy(self, putaway_location, quant, product):
        package_storage_type = False
        if quant:
            package_storage_type = quant.package_id.package_storage_type_id
        if not package_storage_type:
            return putaway_location
        dest_location = putaway_location or self
        package_locations = self.env["stock.storage.location.sequence"].search(
            [
                ("package_storage_type_id", "=", package_storage_type.id),
                ("location_id", "child_of", dest_location.ids),
            ]
        )
        for pack_loc in package_locations:
            pref_loc = pack_loc.location_id
            if (
                pref_loc.pack_putaway_strategy == "none"
                and pref_loc._package_storage_type_allowed(
                    package_storage_type, quant, product
                )
            ):
                return pref_loc
            storage_locations = pref_loc.get_storage_locations(products=product)
            allowed_location = storage_locations.select_first_allowed_location(
                package_storage_type, quant, product
            )
            if allowed_location:
                return allowed_location
        return putaway_location

    def get_storage_locations(self, products=None):
        # TODO support multiple products? cf ABC
        self.ensure_one()
        locations = self.browse()
        if self.pack_putaway_strategy == "none":
            locations = self
        elif self.pack_putaway_strategy == "ordered_locations":
            locations = self._get_ordered_children_locations()
        return locations

    def select_first_allowed_location(self, package_storage_type, quants, products):
        for location in self:
            if location._package_storage_type_allowed(
                package_storage_type, quants, products
            ):
                return location
        return self.browse()

    def select_allowed_locations(self, package_storage_type, quants, products):
        # TODO merge with select_first_allowed_location ?
        allowed_ids = set()
        for location in self:
            if location._package_storage_type_allowed(
                package_storage_type, quants, products
            ):
                allowed_ids.add(location.id)
        return self.browse(allowed_ids)

    def _get_ordered_children_locations(self):
        return self.children_ids

    def _package_storage_type_allowed(self, package_storage_type, quants, products):
        self.ensure_one()
        matching_location_storage_types = self.allowed_location_storage_type_ids.filtered(
            lambda slst: package_storage_type in slst.package_storage_type_ids
        )
        allowed_location_storage_types = self.filter_restrictions(
            matching_location_storage_types, quants, products
        )
        return (
            not self.allowed_location_storage_type_ids or allowed_location_storage_types
        )

    def filter_restrictions(self, matching_location_storage_types, quants, products):
        allowed_location_storage_types = self.env["stock.location.storage.type"]
        for location_storage_type in matching_location_storage_types:
            if self._filter_properties(
                location_storage_type, quants, products
            ) and self._filter_capacity(location_storage_type, quants):
                allowed_location_storage_types |= location_storage_type
        return allowed_location_storage_types

    def _filter_properties(self, location_storage_type, quants, products):
        if location_storage_type.only_empty:
            if not self._existing_quants() and not self._existing_planned_moves():
                return location_storage_type
        elif location_storage_type.do_not_mix_products:
            if location_storage_type.do_not_mix_lots:
                lot = quants.mapped('lot_id')
                if len(lot) > 1:
                    return False
                if not self._existing_quants(
                    products=products, lot=lot
                ) and not self._existing_planned_moves(products=products, lot=lot):
                    return location_storage_type
            else:
                if not self._existing_quants(
                    products=products
                ) and not self._existing_planned_moves(products=products):
                    return location_storage_type
        else:
            return location_storage_type

    def _filter_capacity(self, location_storage_type, quants):
        if self._max_height_allowed(
            location_storage_type, quants
        ) and self._max_weight_allowed(location_storage_type, quants):
            return location_storage_type
        else:
            return self.env["stock.location.storage.type"]

    def _max_height_allowed(self, location_storage_type, quants):
        height = quants.package_id.height
        max_height = location_storage_type.max_height
        return not (max_height and height and height > max_height)

    def _max_weight_allowed(self, location_storage_type, quants):
        pack_weight = quants.package_id.pack_weight
        max_weight = location_storage_type.max_weight
        return not (max_weight and pack_weight and pack_weight > max_weight)

    def _existing_quants(self, products=None, lot=None):
        base_domain = [("location_id", "child_of", self.id)]
        domain = self._prepare_existing_domain(base_domain, products=products, lot=lot)
        return self.env["stock.quant"].search(domain, limit=1)

    def _existing_planned_moves(self, products=None, lot=None):
        base_domain = [
            ("location_dest_id", "child_of", self.id),
            ("move_id.state", "not in", ("draft", "cancel", "done")),
        ]
        domain = self._prepare_existing_domain(base_domain, products=products, lot=lot)
        return self.env["stock.move.line"].search(domain, limit=1)

    def _prepare_existing_domain(self, base_domain, products=None, lot=None):
        domain = base_domain
        if products is not None:
            extra_domain = [("product_id", "not in", products.ids)]
            if lot is not None:
                extra_domain = OR([extra_domain, [("lot_id", "!=", lot.id)]])
            domain = AND([domain, extra_domain])
        return domain
