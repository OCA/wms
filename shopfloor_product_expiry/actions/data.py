# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields

from odoo.addons.component.core import Component


class DataAction(Component):
    _inherit = "shopfloor.data.action"

    def move_line(self, record, with_picking=False, **kw):
        data = super().move_line(record, with_picking=with_picking, **kw)
        if "expiration_date" in kw:
            value = record.expiration_date or None
            if value:
                value = fields.Datetime.to_datetime(value).isoformat()
            data["expiration_date"] = value
        return data
