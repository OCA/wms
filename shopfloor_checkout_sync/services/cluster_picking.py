# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

from odoo.addons.component.core import Component


class ClusterPicking(Component):
    _inherit = "shopfloor.cluster.picking"

    def _has_to_sync_destination(self, lines):
        # we assume that if the destination is already a bin location,
        # the sync has already been done
        return any(line.location_dest_id.child_ids for line in lines)

    def _unload_scan_destination_lock_lines(self, lines):
        if self._has_to_sync_destination(lines):
            dest_pickings = lines.move_id._moves_to_sync_checkout()
            all_moves = self.env["stock.move"].union(*dest_pickings.values())
            # add lock on all the lines that will be synchronized on the
            # destination so other transactions will wait before trying to
            # change the destination
            lines = lines | all_moves.move_line_ids
        super()._unload_scan_destination_lock_lines(lines)

    def _unload_write_destination_on_lines(self, lines, location):
        if self._has_to_sync_destination(lines):
            self._sync_checkout(lines.mapped("move_id"), location)
        return super()._unload_write_destination_on_lines(lines, location)

    def _sync_checkout(self, moves, location):
        dest_pickings = moves._moves_to_sync_checkout()
        all_moves = self.env["stock.move"].union(*dest_pickings.values())
        all_moves.sync_checkout_destination(location)
