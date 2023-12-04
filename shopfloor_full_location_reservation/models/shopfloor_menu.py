# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ShopfloorMenu(models.Model):
    _inherit = "shopfloor.menu"

    full_location_reservation_is_possible = fields.Boolean(
        compute="_compute_full_location_reservation_is_possible"
    )
    full_location_reservation = fields.Boolean(
        string="Process full location reservation",
        default=False,
        help=(
            "If you tick this box, a full location reservation "
            "is triggered for each move_lines location which was found."
        ),
    )

    @api.depends("scenario_id")
    def _compute_full_location_reservation_is_possible(self):
        for menu in self:
            menu.full_location_reservation_is_possible = menu.scenario_id.has_option(
                "full_location_reservation"
            )
