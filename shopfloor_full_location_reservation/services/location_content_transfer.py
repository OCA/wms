# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class LocationContentTransfer(Component):
    _inherit = "shopfloor.location.content.transfer"

    def _find_location_move_lines_from_scan_location(self, *args, **kwargs):
        move_lines = super()._find_location_move_lines_from_scan_location(
            *args, **kwargs
        )
        if not self.work.menu.full_location_reservation:
            return move_lines

        if any(move_lines.move_id.mapped("is_full_location_reservation")):
            return move_lines

        move_lines |= move_lines.move_id._full_location_reservation().move_line_ids
        return move_lines.exists()

    def _move_lines_cancel_work(self, move_lines):
        res = super()._move_lines_cancel_work(move_lines)
        if not self.work.menu.full_location_reservation:
            return res
        move_lines.move_id.undo_full_location_reservation()
        return res
