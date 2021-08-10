# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

from odoo.addons.component.core import Component


class LocationContentTransfer(Component):
    _inherit = "shopfloor.location.content.transfer"

    @property
    def checkout_sync(self):
        return self._actions_for("checkout.sync")

    def _lock_lines(self, lines):
        super()._lock_lines(self.checkout_sync._all_lines_to_lock(lines))

    def _write_destination_on_lines(self, lines, location):
        self.checkout_sync._sync_checkout(lines, location)
        return super()._write_destination_on_lines(lines, location)
