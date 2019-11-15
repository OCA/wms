# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import api, models, fields
from odoo.osv.expression import AND, OR


class StockLocation(models.Model):

    _inherit = 'stock.location'

    pack_storage_strategy = fields.Selection(
        selection=[('none', 'None'),
                   ('ordered_locations', 'Ordered Children Locations')],
        required=True,
        default='none',
        string='Packs storage strategy',
        help='TODO',
    )
    display_pack_storage_strategy = fields.Boolean(
        compute='_compute_display_pack_storage_strategy'
    )

    @api.depends(
        'child_ids', 'location_id', 'location_id.pack_storage_strategy',
        'location_id.display_pack_storage_strategy'
    )
    def _compute_display_pack_storage_strategy(self):
        for location in self:
            # Do not display on locations without children
            if not location.child_ids:
                location.display_pack_storage_strategy = False
                continue
            current_location = location.location_id
            display = True
            while current_location:
                # If a parent has pack_storage_strategy set, we don't display
                # it on its children
                if current_location.pack_storage_strategy != 'none':
                    display = False
                    break
                current_location = current_location.location_id
            location.display_pack_storage_strategy = display

    def _get_putaway_rule_location(self, product=None, category=None):
        """Get the destination location from putaway rules"""
        quant = self.env.context.get('putaway_quant')
        package_storage_type = False
        if quant:
            package_storage_type = quant.package_id.stock_package_storage_type_id
        if not package_storage_type:
            return super()._get_putaway_rule_location(
                product=product, category=category
            )
        putaway_rules = self.putaway_rule_ids.filter_rules(
            product=product, category=category
        )
        if category and not product:
            product = quant.product_id
        for rule in putaway_rules:
            dest_location = rule._get_destination_location()
            if (
                dest_location.pack_storage_strategy == 'none' and
                dest_location._package_storage_type_allowed(
                    package_storage_type, quant, product=product
                )
            ):
                return dest_location
            storage_locations = dest_location.get_storage_locations(
                product=product
            )
            allowed_location = storage_locations.select_first_allowed_location(
                package_storage_type, quant, product=product
            )
            if allowed_location:
                return allowed_location
        return self.browse()

    def get_storage_locations(self, product=None):
        self.ensure_one()
        locations = self.browse()
        if self.pack_storage_strategy == 'none':
            locations = self
        elif self.pack_storage_strategy == 'ordered_locations':
            locations = self._get_ordered_children_locations()
        return locations

    def select_first_allowed_location(self, package_storage_type, quant, product=None):
        for location in self:
            if (
                location._package_storage_type_allowed(
                    package_storage_type, quant, product=product
                )
            ):
                return location
        return self.browse()

    def _get_ordered_children_locations(self):
        return self.search(
            [('id', 'child_of', self.ids), ('id', '!=', self.id)]
        )

    def _package_storage_type_allowed(self, package_storage_type, quant, product=None):
        self.ensure_one()
        matching_location_storage_types = self.allowed_stock_location_storage_type_ids.filtered(
            lambda slst: package_storage_type in slst.stock_package_storage_type_ids
        )
        allowed_location_storage_types = self.filter_restrictions(
            matching_location_storage_types, quant, product=product
        )
        return not self.allowed_stock_location_storage_type_ids or allowed_location_storage_types

    def filter_restrictions(self, matching_location_storage_types, quant, product=None):
        allowed_location_storage_types = self.env['stock.location.storage.type']
        for location_storage_type in matching_location_storage_types:
            if location_storage_type.only_empty:
                if (
                    not self._existing_quants() and
                    not self._existing_planned_moves()
                ):
                    allowed_location_storage_types |= location_storage_type
            elif location_storage_type.do_not_mix_products:
                if location_storage_type.do_not_mix_lots:
                    lot = quant.lot_id
                    if (
                        not self._existing_quants(product=product, lot=lot) and
                        not self._existing_planned_moves(
                            product=product, lot=lot
                        )
                    ):
                        allowed_location_storage_types |= location_storage_type
                else:
                    if (
                        not self._existing_quants(product=product) and
                        not self._existing_planned_moves(product=product)
                    ):
                        allowed_location_storage_types |= location_storage_type
            else:
                allowed_location_storage_types |= location_storage_type
        return allowed_location_storage_types

    def _existing_quants(self, product=None, lot=None):

        base_domain = [('location_id', '=', self.id)]
        domain = self._prepare_existing_domain(
            base_domain, product=product, lot=lot
        )
        return self.env['stock.quant'].search(domain, limit=1)

    def _existing_planned_moves(self, product=None, lot=None):
        base_domain = [
            ('location_dest_id', '=', self.id),
            ('move_id.state', 'not in', ('draft', 'cancel', 'done'))
        ]
        domain = self._prepare_existing_domain(
            base_domain, product=product, lot=lot
        )
        return self.env['stock.move.line'].search(domain, limit=1)

    def _prepare_existing_domain(self, base_domain, product=None, lot=None):
        domain = base_domain
        if product is not None:
            extra_domain = [('product_id', '!=', product.id)]
            if lot is not None:
                extra_domain = OR([extra_domain, [('lot_id', '!=', lot.id)]])
            domain = AND([domain, extra_domain])
        return domain
