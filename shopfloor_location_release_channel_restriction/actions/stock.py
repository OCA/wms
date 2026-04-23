# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.addons.component.core import Component


class StockAction(Component):
    """Provide methods to work with stock operations."""

    _inherit = "shopfloor.stock.action"

    def _set_release_channel_restriction(self, lines):
        lines._set_release_channel_current_restriction()

    def set_destination_on_lines(self, lines, location_dest):
        res = super().set_destination_on_lines(lines, location_dest)
        self._set_release_channel_restriction(lines)
        return res
