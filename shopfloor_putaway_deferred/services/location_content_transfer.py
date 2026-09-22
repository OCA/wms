# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.addons.component.core import Component


class LocationContentTransfer(Component):

    _inherit = "shopfloor.location.content.transfer"

    def _select_move_lines_first_location(self, move_lines):
        result = super()._select_move_lines_first_location(move_lines=move_lines)
        to_recompute = result.filtered(lambda ml: ml.putaway_deferred)
        to_recompute._recompute_putaways()
        return result
