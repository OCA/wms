# Copyright 2019 Camptocamp (https://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    need_release = fields.Boolean(compute="_compute_need_release")

    @api.depends("move_lines.need_release")
    def _compute_need_release(self):
        for picking in self:
            picking.need_release = any(move.need_release for move in picking.move_lines)

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
