# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import _, api, models
from odoo.exceptions import UserError
from odoo.tools import groupby


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    def _action_done(self):
        # Check before acton_done because the reservation for the next picking
        # Will not have happen yet (in stock.move _action_done)
        # The quantity will still be available in the quants
        self._check_same_order_at_destination()
        return super()._action_done()

    @api.model
    def _raise_error_unique_order_per_location(self, locations):
        raise UserError(
            _(
                "The location(s) {} can only accept goods for the same sales order.".format(
                    {", ".join(locations.mapped("name"))}
                )
            )
        )

    def _check_same_order_at_destination(self, location=None):
        for picking, move_lines in groupby(self, lambda line: line.picking_id):
            if not picking.picking_type_id.same_next_picking:
                continue
            move_lines = self.browse().union(*move_lines)
            destination_locations = location or move_lines.location_dest_id
            locations_available = destination_locations.filtered(
                lambda location: any(location.quant_ids.mapped("available_quantity"))
            )
            if locations_available:
                self._raise_error_unique_order_per_location(locations_available)
            domain = self._same_order_at_destination_move_line_domain(
                move_lines, destination_locations
            )
            lines = self.env["stock.move.line"].search(domain)
            if not lines:
                continue
            self._raise_error_unique_order_per_location(destination_locations)

    def _same_order_at_destination_move_line_domain(self, move_lines, locations):
        return [
            ("location_id", "child_of", locations.ids),
            (
                "state",
                "in",
                (
                    "assigned",
                    "partially_available",
                ),
            ),
            # Search for lines at location not in the next picking
            (
                "move_id.id",
                "not in",
                move_lines.move_id.move_dest_ids.picking_id.move_lines.ids,
            ),
        ]
