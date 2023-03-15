# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from odoo.addons.component.core import Component


class Reception(Component):
    _inherit = "shopfloor.reception"

    def _data_for_stock_picking(self, picking, with_lines=False, **kw):
        if "with_purchase_order" not in kw:
            kw["with_purchase_order"] = True
        return super()._data_for_stock_picking(picking, with_lines, **kw)
