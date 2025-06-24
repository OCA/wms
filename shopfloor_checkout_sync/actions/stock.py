# Copyright 2024 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.component.core import Component


class StockAction(Component):
    _inherit = "shopfloor.stock.action"

    def _set_destination_on_lines(self, lines, location_dest):
        checkout_sync = self._actions_for("checkout.sync")
        checkout_sync._sync_checkout(lines, location_dest)
        super()._set_destination_on_lines(lines, location_dest)

    def set_destination_and_unload_lines(self, lines, location_dest, unload=False):
        checkout_sync = self._actions_for("checkout.sync")
        all_lines = checkout_sync._all_lines_to_lock(lines)
        super().set_destination_and_unload_lines(all_lines, location_dest, unload)
