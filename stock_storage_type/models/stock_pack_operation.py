# -*- coding: utf-8 -*-
# Copyright 2020 Camptocamp SA
# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json
from collections import defaultdict

from odoo import api, fields, models


class StockPackOperation(models.Model):

    _inherit = "stock.pack.operation"
    # We use a domain with the module 'web_domain_field', because if we use a
    # many2many with a domain in the view, the onchange updating the many2many
    # client side blocks the browser for several seconds if we have thousands
    # of locations.
    allowed_location_dest_domain = fields.Char(
        string="Allowed Destinations Domain",
        compute="_compute_allowed_location_dest_domain",
    )

    implied_product_ids = fields.Many2many(
        "product.product",
        compute="_compute_implied_products_and_lots",
        help="technical field: list of product implied by the pack operation",
    )

    implied_lot_ids = fields.Many2many(
        "stock.production.lot",
        compute="_compute_implied_products_and_lots",
        help="technical field: list of lots implied by the pack operation",
    )

    # in odoo > 10, this field is a stored related on stock.move.line.
    # Even id the state here has not the same meaning as in odoo > 10,
    # we also need to store it to have a simple way to filter stock packaging
    # already processed or not more valid. If the picking is done or cancelled
    # the pack operation is no more relevant to know if a qty will reach or
    # quit a stock.location
    state = fields.Selection(store=True, index=True)

    @api.depends("product_id", "package_id", "pack_lot_ids")
    def _compute_implied_products_and_lots(self):
        ProductProduct = self.env["product.product"]
        StockProductionLot = self.env["stock.production.lot"]
        for record in self:
            quants = record.package_id.get_content()
            record.implied_product_ids = ProductProduct.browse(
                record.product_id.ids + quants.mapped("product_id").ids
            )
            record.implied_lot_ids = StockProductionLot.browse(
                record.pack_lot_ids.mapped("lot_id").ids + quants.mapped("lot_id").ids
            )

    @api.depends(
        "package_id",
        "package_id.package_storage_type_id",
        "package_id.package_storage_type_id.location_storage_type_ids",
        "package_id.package_storage_type_id.storage_location_sequence_ids",
        "package_id.package_storage_type_id.storage_location_sequence_ids.location_id",
        "package_id.package_storage_type_id.storage_location_sequence_ids.location_id.leaf_location_ids",
        # noqa
        # Dependency on quant_ids managed by cache invalidation on create/write
        "picking_id",
        "picking_id.location_dest_id",
        "picking_id.pack_operation_ids.location_dest_id",
    )
    def _compute_allowed_location_dest_domain(self):
        # TODO Add some JS to refresh the domain after changing on a line ?
        for pack_level in self:
            picking_child_location_dest_ids = self.env["stock.location"].search(
                [("id", "child_of", pack_level.picking_id.location_dest_id.id)]
            )
            # For outgoing type, we don't set the location dest so avoid
            # computing the domain
            if (
                pack_level.package_id.package_storage_type_id
                and pack_level.picking_id.picking_type_code != "outgoing"
            ):
                allowed_locations = pack_level._get_allowed_location_dest_ids()
                # TODO check if intersect is needed as we use picking dest loc
                #  in _get_allowed_location_dest_ids
                intersect_locations = (
                    allowed_locations & picking_child_location_dest_ids
                )
                # Add the pack_level actual location_dest since it is actually
                # excluded by the check on incoming stock moves
                intersect_locations |= pack_level.location_dest_id
                pack_level.allowed_location_dest_domain = json.dumps(
                    [("id", "in", intersect_locations.ids)]
                )
            elif isinstance(pack_level.id, models.NewId):
                pack_level.allowed_location_dest_domain = json.dumps(
                    [("id", "in", pack_level.picking_id.location_dest_id.ids)]
                )
            else:
                pack_level.allowed_location_dest_domain = json.dumps(
                    [("id", "in", picking_child_location_dest_ids.ids)]
                )

    def _get_allowed_location_dest_ids(self):
        package_locations = self.env["stock.storage.location.sequence"].search(
            [
                (
                    "package_storage_type_id",
                    "=",
                    self.package_id.package_storage_type_id.id,
                ),
                ("location_id", "child_of", self.picking_id.location_dest_id.id),
            ]
        )
        all_allowed_locations = set()
        products = self.implied_product_ids
        for pack_loc in package_locations:
            pref_loc = pack_loc.location_id
            storage_locations = pref_loc.get_storage_locations(products=products)
            allowed_locations = storage_locations.select_allowed_locations(
                self.package_id.package_storage_type_id,
                self.package_id.quant_ids,
                products,
            )
            all_allowed_locations.update(allowed_locations.ids)
        return self.env["stock.location"].browse(all_allowed_locations)

    def recompute_pack_putaway(self):
        for level in self:
            if not level.package_id.quant_ids:
                continue
            level.location_dest_id = level.location_dest_id._get_pack_putaway_strategy(
                level.location_dest_id,
                level.package_id.quant_ids,
                level.implied_product_ids,
            )

    @api.model
    def _finalize_pack_putaway_strategy(self, vals):
        StockQuantPackage = self.env["stock.quant.package"]
        StockLocation = self.env["stock.location"]
        StockPicking = self.env["stock.picking"]
        ProductProduct = self.env["product.product"]

        product_id = vals.get("product_id")
        package_id = vals.get("package_id")
        quant = None
        product = None
        if product_id:
            product = ProductProduct.browse(product_id)
            reserved_quants_by_products = defaultdict(set)
            picking = StockPicking.browse(vals["picking_id"])
            moves = picking.move_lines.filtered(
                lambda move: move.state in ("assigned", "confirmed", "waiting")
            )
            for q in moves.mapped("reserved_quant_ids"):
                reserved_quants_by_products[q.product_id].add(q)
            reserved_quants = reserved_quants_by_products.get(product, [])
            quant = len(reserved_quants) == 1 and next(iter(reserved_quants)) or None
        elif package_id:
            quant_package = StockQuantPackage.browse(package_id)
            if not quant_package.single_product_id:
                return
            product = quant_package.single_product_id
            # we take the first quant since we are only interested by the
            # package_id on the quant
            quant = quant_package.get_content()[:1]
            if not quant:
                return
        if not quant or not product:
            return

        putaway_location = StockLocation.browse(vals["location_dest_id"])
        location_dest_id = putaway_location._get_pack_putaway_strategy(
            putaway_location, quant, product
        ).id
        vals["location_dest_id"] = location_dest_id

    @api.model
    def create(self, vals):
        self._finalize_pack_putaway_strategy(vals)
        res = super(StockPackOperation, self).create(vals)
        locations = res.location_id | res.location_dest_id
        locations.invalidate_cache(
            ["in_move_line_ids", "out_move_line_ids"], locations.ids
        )
        locations._tigger_cache_recompute_if_required()
        return res

    def write(self, vals):
        location_ids = []
        if "location_id" in vals:
            location_ids.extend(self.mapped("location_id").ids)
        if "location_dest_id" in vals:
            location_ids.extend(self.mapped("location_dest_id").ids)
        res = super(StockPackOperation, self).write(vals)
        location_ids.extend(self.mapped("location_id").ids)
        location_ids.extend(self.mapped("location_dest_id").ids)
        locations = self.env["stock.location"].browse(location_ids)
        if "state" in vals:
            locations.invalidate_cache(
                ["in_move_line_ids", "out_move_line_ids"], locations.ids
            )
        locations._tigger_cache_recompute_if_required()
        return res

    def unlink(self):
        locations = self.mapped("location_id") | self.mapped("location_dest_id")
        res = super(StockPackOperation, self).unlink()
        locations.invalidate_cache(
            ["in_move_line_ids", "out_move_line_ids"], locations.ids
        )
        locations._tigger_cache_recompute_if_required()
        return res
