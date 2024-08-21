# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class LocationContentTransfer(Component):
    _inherit = "shopfloor.location.content.transfer"

    def _select_move_lines_first_location(self, move_lines):
        if not self.work.menu.full_location_reservation:
            return super()._select_move_lines_first_location(move_lines)

        if any(move_lines.move_id.mapped("is_full_location_reservation")):
            return super()._select_move_lines_first_location(move_lines)

        move_lines = super()._select_move_lines_first_location(move_lines)
        move_lines |= move_lines._full_location_reservation().move_line_ids

        # As lines should concern only one source location and as lines
        # can have been split, we need to retrieve only those with first location
        move_lines = super()._select_move_lines_first_location(move_lines.exists())
        return move_lines.exists()

    def _move_lines_cancel_work(self, move_lines):
        res = super()._move_lines_cancel_work(move_lines)
        if not self.work.menu.full_location_reservation:
            return res
        move_lines.move_id.undo_full_location_reservation()
        return res
