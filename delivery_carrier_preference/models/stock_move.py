# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from itertools import groupby

from odoo import api, fields, models, tools


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
        "ordered_available_to_promise_uom_qty",
    )
    def _compute_estimated_shipping_weight(self):
        for move in self:
            prod = move.product_id
            move.estimated_shipping_weight = prod.get_total_weight_from_packaging(
                move.ordered_available_to_promise_uom_qty
            )

    def _get_new_picking_values(self):
        vals = super()._get_new_picking_values()
        # Take the carrier_id from the group only when we have a related line
        # (i.e. we are in an OUT). It reflects the code of the super method in
        # "delivery" which takes the carrier of the related SO through SO line
        if self.sale_line_id:
            group_carrier = self.mapped("group_id.carrier_id")
            if group_carrier:
                vals["carrier_id"] = group_carrier.id
        return vals

    @staticmethod
    def _filter_recompute_preferred_carrier(move):
        precision = move.env["decimal.precision"].precision_get(
            "Product Unit of Measure"
        )
        return (
            move.need_release
            # do not change the carrier is nothing can be released on the stock move
            and not tools.float_is_zero(
                move.ordered_available_to_promise_uom_qty, precision_digits=precision
            )
            and move.rule_id.route_id.force_recompute_preferred_carrier_on_release
        )

    def release_available_to_promise(self):
        modified_groups = {}
        for picking in self.filtered(self._filter_recompute_preferred_carrier).mapped(
            "picking_id"
        ):
            if picking.picking_type_code != "outgoing":
                continue
            picking.add_preferred_carrier()

        # if we have other pickings in the same group and now they have different
        # carriers, split them in 2 groups and sync the carrier on their group
        sorted_pickings = self.mapped("picking_id").sorted(
            lambda pick: (pick.group_id, pick.carrier_id)
        )
        for (group, new_carrier), iter_pickings in groupby(
            sorted_pickings, lambda pick: (pick.group_id, pick.carrier_id)
        ):
            pickings = self.env["stock.picking"].union(*iter_pickings)
            if group.carrier_id != new_carrier:
                # always create a new procurement group when we change carrier,
                # the old group will be reassigned to the backorders if any,
                # otherwise it will stay empty in the depths of nothingness
                new_group = group.copy(
                    default={"name": "{} ({})".format(group.name, new_carrier.name)}
                )
                pickings.move_lines.group_id = new_group

                # sync carrier
                new_group.carrier_id = new_carrier
                modified_groups[new_group] = group

        res = super().release_available_to_promise()

        for new_group, original_group in modified_groups.items():
            # these are backorders created for unavailable qties,
            # reassign them the original group and carrier
            need_release_pickings = new_group.picking_ids.filtered("need_release")
            # reassign the original group and carriers on the backorders
            need_release_pickings.move_lines.group_id = original_group
            need_release_pickings.carrier_id = original_group.carrier_id

        return res
