# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.addons.component.core import Component


class ShopfloorSchemaAction(Component):
    _inherit = "shopfloor.schema.action"

    def picking(self):
        schema = super().picking()
        schema.update(
            {"helpdesk_ticket_allowed": {"required": False, "type": "boolean"}}
        )
        return schema
