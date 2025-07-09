# Copyright 2025 ACSONE SA/NV (https://acsone.eu)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.addons.component.core import Component


class DataAction(Component):
    _inherit = "shopfloor.data.action"

    def move_line(self, record, with_picking=False, **kw):
        result = super().move_line(record, with_picking=with_picking, **kw)
        if "lot_name" in kw:
            result.update(
                {
                    "lot_name": record.lot_name or None,
                }
            )
        return result
