# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    is_full_location_reservation_visible = fields.Boolean(
        "Is full location reservation visible",
        related="picking_type_id.is_full_location_reservation_visible",
    )
    has_full_location_reservations = fields.Boolean(
        "Has full location reservations",
        compute="_compute_has_full_location_reservations",
    )

    @api.depends("move_lines.is_full_location_reservation")
    def _compute_has_full_location_reservations(self):
        for rec in self:
            rec.has_full_location_reservations = (
                rec.move_lines.filtered(lambda m: m.is_full_location_reservation)
                and True
                or False
            )

    def do_full_location_reservation(self):
        self.move_lines._full_location_reservation()

    def undo_full_location_reservation(self):
        self.move_lines.undo_full_location_reservation()
