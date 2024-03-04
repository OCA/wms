# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)


from odoo.addons.component.core import Component


class Reception(Component):
    _inherit = "shopfloor.reception"

    def _data_for_move_lines(self, lines, **kw):
        kw["display_vendor_packaging"] = self.work.menu.display_vendor_packaging
        return super()._data_for_move_lines(lines, **kw)

    def _data_for_moves(self, moves, **kw):
        kw["display_vendor_packaging"] = self.work.menu.display_vendor_packaging
        return super()._data_for_moves(moves, **kw)
