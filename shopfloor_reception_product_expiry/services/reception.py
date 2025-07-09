# Copyright 2025 ACSONE SA/NV (https://acsone.eu)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from odoo.addons.component.core import Component


class Reception(Component):

    _inherit = "shopfloor.reception"

    def _data_for_move_lines(self, lines, **kw):
        kw.update({"expiration_date": True})
        return super()._data_for_move_lines(lines, **kw)
