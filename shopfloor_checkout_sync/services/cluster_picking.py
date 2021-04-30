# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

from odoo.addons.component.core import Component


class ClusterPicking(Component):
    _inherit = "shopfloor.cluster.picking"

    @property
    def checkout_sync(self):
        return self._actions_for("checkout.sync")

    def _lock_lines(self, lines):
        super()._lock_lines(self.checkout_sync._all_lines_to_lock(lines))

    def _unload_write_destination_on_lines(self, lines, location):
        self.checkout_sync._sync_checkout(lines, location)
        return super()._unload_write_destination_on_lines(lines, location)
