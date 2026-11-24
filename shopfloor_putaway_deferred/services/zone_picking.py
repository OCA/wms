# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.addons.component.core import Component


class ZonePicking(Component):
    _inherit = "shopfloor.zone.picking"

    def _response_for_set_line_destination(self, move_line, **kw):
        if move_line.putaway_deferred:
            move_line._recompute_putaways()
        return super()._response_for_set_line_destination(move_line, **kw)
