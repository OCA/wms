# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import api, fields, models


class StockPackageLevel(models.Model):

    _inherit = "stock.package_level"

    allowed_location_dest_ids = fields.Many2many(
        "stock.location",
        compute="_compute_allowed_location_dest_ids",
        string="Allowed destinations",
    )

    @api.depends(
        "package_id",
        "package_id.package_storage_type_id",
        "package_id.package_storage_type_id.location_storage_type_ids",
        "package_id.package_storage_type_id.storage_location_sequence_ids",
        "package_id.package_storage_type_id.storage_location_sequence_ids.location_id",
        "package_id.package_storage_type_id.storage_location_sequence_ids.location_id.leaf_location_ids",  # noqa
        # Dependency on quant_ids managed by cache invalidation on create/write
        "picking_id",
        "picking_id.location_dest_id",
        "picking_id.package_level_ids.location_dest_id",
    )
    def _compute_allowed_location_dest_ids(self):
        # TODO Add some JS to refresh the domain after changing on a line ?
        for pack_level in self:
            picking_child_location_dest_ids = self.env["stock.location"].search(
                [("id", "child_of", pack_level.picking_id.location_dest_id.id)]
            )
            # For outgoing type, we don't set the location dest so avoid
            # computing the domain
            if (
                pack_level.package_id.package_storage_type_id
                and pack_level.picking_type_code != "outgoing"
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
                pack_level.allowed_location_dest_ids = intersect_locations.ids
            elif isinstance(pack_level.id, models.NewId):
                pack_level.allowed_location_dest_ids = (
                    pack_level.picking_id.location_dest_id.ids
                )
            else:
                pack_level.allowed_location_dest_ids = (
                    picking_child_location_dest_ids.ids
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
        products = self.mapped("move_line_ids.product_id")
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
