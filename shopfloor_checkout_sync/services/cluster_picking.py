# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

from odoo.addons.component.core import Component


class ClusterPicking(Component):
    _inherit = "shopfloor.cluster.picking"

    def _unload_set_destination_on_lines(self, lines, location):
        self._sync_checkout(lines.mapped("move_id"), location)
        return super()._unload_set_destination_on_lines(lines, location)

    def _sync_checkout(self, moves, location):
        dest_pickings = moves._moves_to_sync_checkout()
        all_moves = self.env["stock.move"].union(*dest_pickings.values())
        all_moves.sync_checkout_destination(location)
