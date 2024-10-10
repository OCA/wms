# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.addons.component.core import Component


class LocationContentTransfer(Component):

    _inherit = "shopfloor.location.content.transfer"

    def _select_move_lines_first_location(self, move_lines):
        move_lines._recompute_putaways()
        return super()._select_move_lines_first_location(move_lines)
