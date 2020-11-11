# Copyright 2019 Camptocamp (https://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, exceptions, fields, models
from odoo.tools.float_utils import float_compare


class StockPicking(models.Model):
    _inherit = "stock.picking"

    need_release = fields.Boolean(
        compute="_compute_need_release", search="_search_need_release",
    )
    release_ready = fields.Boolean(
        compute="_compute_release_ready", search="_search_release_ready",
    )

    @api.depends("move_lines.need_release")
    def _compute_need_release(self):
        for picking in self:
            picking.need_release = any(move.need_release for move in picking.move_lines)

    def _search_need_release(self, operator, value):
        if (operator, value) != ("=", True):
            raise exceptions.UserError(
                _("Unsupported search: %s %s") % (operator, value)
            )
        groups = self.env["stock.move"].read_group(
            [("need_release", operator, value)], ["picking_id"], ["picking_id"]
        )
        return [("id", "in", [group["picking_id"][0] for group in groups])]

    @api.depends("move_lines.ordered_available_to_promise_qty")
    def _compute_release_ready(self):
        for picking in self:
            if not picking.need_release:
                picking.release_ready = False
                picking.release_ready_count = 0
                continue
            if picking.move_type == "one":
                picking.release_ready = all(
                    float_compare(
                        move.ordered_available_to_promise_qty,
                        move.product_qty,
                        precision_rounding=move.product_id.uom_id.rounding,
                    )
                    == 0
                    for move in picking.move_lines
                )
            else:
                picking.release_ready = any(
                    move.ordered_available_to_promise_qty > 0
                    for move in picking.move_lines
                )

    def _search_release_ready(self, operator, value):
        if operator != "=":
            raise exceptions.UserError(_("Unsupported operator %s") % (operator,))
        # if we search moves with a promise qty > 0, we restrict
        # the number of moves / pickings to filter afterwards
        moves = self.env["stock.move"].search(
            [("ordered_available_to_promise_uom_qty", ">", 0)]
        )
        pickings = moves.picking_id.filtered("release_ready")
        return [("id", "in", pickings.ids)]

    def release_available_to_promise(self):
        # When the stock.picking form view is opened through the "Deliveries"
        # button of a sale order, the latter sets values in the context such as
        # default_picking_id default_origin, ... Clean up these values
        # otherwise they make the release misbehave.
        context = {
            key: value
            for key, value in self.env.context.items()
            if not key.startswith("default_")
        }
        self.mapped("move_lines").with_context(context).release_available_to_promise()

    def _release_link_backorder(self, origin_picking):
        self.backorder_id = origin_picking
        origin_picking.message_post(
            body=_(
                "The backorder <a href=# data-oe-model=stock.picking"
                " data-oe-id=%d>%s</a> has been created."
            )
            % (self.id, self.name)
        )
