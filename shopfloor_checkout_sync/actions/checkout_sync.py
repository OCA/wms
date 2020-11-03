# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

from odoo.addons.component.core import Component


class CheckoutSyncAction(Component):
    """Provide methods sync destination location on checkout/packing
    """

    _name = "shopfloor.checkout.sync.action"
    _inherit = "shopfloor.process.action"
    _usage = "checkout.sync"

    def _has_to_sync_destination(self, lines):
        # we assume that if the destination is already a bin location,
        # the sync has already been done
        return any(line.location_dest_id.child_ids for line in lines)

    def _all_lines_to_lock(self, lines):
        if self._has_to_sync_destination(lines):
            dest_pickings = lines.move_id._moves_to_sync_checkout()
            all_moves = self.env["stock.move"].union(*dest_pickings.values())
            # add lock on all the lines that will be synchronized on the
            # destination so other transactions will wait before trying to
            # change the destination
            lines = lines | all_moves.move_line_ids
        return lines

    def _sync_checkout(self, lines, location):
        moves = lines.mapped("move_id")
        if self._has_to_sync_destination(lines):
            dest_pickings = moves._moves_to_sync_checkout()
            all_moves = self.env["stock.move"].union(*dest_pickings.values())
            all_moves.sync_checkout_destination(location)
