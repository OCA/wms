# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import _, api, exceptions, fields, models


class StockQuantPackage(models.Model):
    _inherit = "stock.quant.package"

    move_line_ids = fields.One2many(
        comodel_name="stock.move.line",
        inverse_name="package_id",
        readonly=True,
        help="Technical field. Move lines moving this package.",
    )
    planned_move_line_ids = fields.One2many(
        comodel_name="stock.move.line",
        inverse_name="result_package_id",
        readonly=True,
        help="Technical field. Move lines for which destination is this package.",
    )
    # TODO: review other fields
    reserved_move_line_ids = fields.One2many(
        comodel_name="stock.move.line", compute="_compute_reserved_move_lines",
    )
    shopfloor_weight = fields.Float(
        "Shopfloor weight (kg)",
        digits="Product Unit of Measure",
        compute="_compute_shopfloor_weight",
        help="Real pack weight or the estimated one.",
    )

    def _get_reserved_move_lines(self):
        return self.env["stock.move.line"].search(
            [("package_id", "=", self.id), ("state", "not in", ("done", "cancel"))]
        )

    @api.depends("move_line_ids.state")
    def _compute_reserved_move_lines(self):
        for rec in self:
            rec.update({"reserved_move_line_ids": rec._get_reserved_move_lines()})

    @api.depends("pack_weight", "estimated_pack_weight")
    @api.depends_context("picking_id")
    def _compute_shopfloor_weight(self):
        for rec in self:
            rec.shopfloor_weight = rec.pack_weight or rec.estimated_pack_weight

    # TODO: we should refactor this like

    # source_planned_move_line_ids
    # destination_planned_move_line_ids

    # filter out done/cancel lines

    @api.constrains("name")
    def _constrain_name_unique(self):
        for rec in self:
            if self.search_count([("name", "=", rec.name), ("id", "!=", rec.id)]):
                raise exceptions.UserError(_("Package name must be unique!"))

    def move_package_to_location(self, dest_location):
        """Create inventories to move a package to a different location

        It should be called when the package is - in real life - already in
        the destination. It creates an inventory to remove the package from
        the source location and a second inventory to place the package
        in the destination (to reflect the reality).

        The source location is the current location of the package.
        """
        quant_values = []
        # sudo and the key in context activate is_inventory_mode on quants
        quants = self.quant_ids.sudo().with_context(inventory_mode=True)
        for quant in quants:
            quantity = quant.quantity
            quant.inventory_quantity = 0
            quant_values.append(
                self._move_package_quant_move_values(quant, dest_location, quantity)
            )

        quant_model = self.env["stock.quant"].sudo().with_context(inventory_mode=True)
        quant_model.create(quant_values)

    def _move_package_quant_move_values(self, quant, location, quantity):
        return {
            "product_id": quant.product_id.id,
            "inventory_quantity": quantity,
            "location_id": location.id,
            "lot_id": quant.lot_id.id,
            "package_id": quant.package_id.id,
            "owner_id": quant.owner_id.id,
        }
