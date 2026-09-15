# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    total_weight = fields.Float(
        compute="_compute_picking_info",
        help="Technical field. Indicates total weight of transfers included.",
    )
    move_line_count = fields.Integer(
        compute="_compute_picking_info",
        help="Technical field. Indicates number of move lines included.",
    )
    package_level_count = fields.Integer(
        compute="_compute_picking_info",
        help="Technical field. Indicates number of package_level included.",
    )
    bulk_line_count = fields.Integer(
        compute="_compute_picking_info",
        help="Technical field. "
        "Indicates number of move lines without package included.",
    )
    is_shopfloor_created = fields.Boolean()

    @api.depends(
        "move_line_ids", "move_line_ids.reserved_qty", "move_line_ids.product_id.weight"
    )
    def _compute_picking_info(self):
        for item in self:
            item.update(
                {
                    "total_weight": item._calc_weight(),
                    "move_line_count": len(item.move_line_ids),
                    "package_level_count": len(item.package_level_ids),
                    # NOTE: not based on 'move_line_ids_without_package' field
                    # on purpose as it also takes into account the
                    # 'Move entire packs' option from the picking type.
                    "bulk_line_count": len(
                        item.move_line_ids.filtered(lambda ml: not ml.package_level_id)
                    ),
                }
            )

    def _calc_weight(self):
        weight = 0.0
        for move_line in self.mapped("move_line_ids"):
            weight += move_line.reserved_qty * move_line.product_id.weight
        return weight

    def _check_move_lines_map_quant_package(self, package):
        # see tests/test_move_action_assign.py for details
        pack_move_lines = self.move_line_ids.filtered(
            lambda ml: ml.package_id == package
        )
        # if we set a qty_done on any line, it's picked, we don't want
        # to change it in any case, so we ignore the package level
        if any(pack_move_lines.mapped("qty_done")):
            return False
        # if we already changed the destination package, do not create
        # a new package level
        if any(
            line.result_package_id != package
            for line in pack_move_lines
            if line.result_package_id
        ):
            return False
        return super()._check_move_lines_map_quant_package(package)

    def _put_in_pack(self, move_line_ids, create_package_level=True):
        """
        Marks the corresponding move lines as 'shopfloor_checkout_done'
        when the package is created in the backend.

        """
        new_package = super()._put_in_pack(move_line_ids, create_package_level)
        lines = move_line_ids.filtered(lambda p: p.result_package_id == new_package)
        lines.write({"shopfloor_checkout_done": True})
        return new_package
