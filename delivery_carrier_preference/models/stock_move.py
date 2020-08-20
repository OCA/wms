# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import api, fields, models


class StockMove(models.Model):

    _inherit = "stock.move"

    estimated_shipping_weight = fields.Float(
        string="Estimated shipping weight",
        compute="_compute_estimated_shipping_weight",
        help="Total weight available to promise calculated according to the"
        " quantity available to promise and weight defined on packagings "
        "for this product.",
    )

    @api.depends(
        "product_id",
        "product_id.packaging_ids",
        "product_id.packaging_ids.max_weight",
        "product_id.weight",
        "ordered_available_to_promise",
    )
    def _compute_estimated_shipping_weight(self):
        for move in self:
            prod = move.product_id
            move.estimated_shipping_weight = prod.get_total_weight_from_packaging(
                move.ordered_available_to_promise
            )

    def release_available_to_promise(self):
        existing_backorders = dict()
        existing_carriers = dict()
        for picking in self.mapped("picking_id"):
            if picking.picking_type_code != "outgoing" or not picking.mapped(
                "move_lines.rule_id.route_id.force_recompute_preferred_carrier_on_release"  # noqa
            ):
                continue
            existing_backorders[picking.id] = picking.mapped("backorder_ids").ids
            existing_carriers[picking.id] = picking.carrier_id.id

            picking.add_preferred_carrier()
            picking.group_id.carrier_id = picking.carrier_id

        res = super().release_available_to_promise()

        for picking in self.mapped("picking_id"):
            if picking.picking_type_code != "outgoing" or not picking.mapped(
                "move_lines.rule_id.route_id.force_recompute_preferred_carrier_on_release"  # noqa
            ):
                continue
            original_carrier = existing_carriers[picking.id]
            if original_carrier and original_carrier != picking.carrier_id:
                new_backorder = picking.backorder_ids.filtered(
                    lambda b: b.id not in existing_backorders.get(picking.id)
                )
                if new_backorder:
                    new_proc_group = picking.group_id.copy()
                    new_backorder.group_id = new_proc_group
                    new_backorder.move_lines.write({"group_id": new_proc_group.id})
                picking.group_id.carrier_id = picking.carrier_id
        return res
