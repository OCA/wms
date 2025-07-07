# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.addons.component.core import Component


class ShopfloorSchemaAction(Component):
    _inherit = "shopfloor.schema.action"

    def move_line(self, with_packaging=False, with_picking=False) -> dict:
        schema = super().move_line(
            with_packaging=with_packaging, with_picking=with_picking
        )
        schema.update(
            {
                "expiration_date": {"type": "string", "required": False},
            }
        )
        return schema
