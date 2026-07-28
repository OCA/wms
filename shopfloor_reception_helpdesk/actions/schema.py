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

    def helpdesk_wizard(self):
        return {
            "id": {"required": True, "type": "integer"},
            "description": {
                "type": "string",
                "nullable": True,
            },
            "motive": self._schema_dict_of(self.helpdesk_motive(), required=False),
        }

    def helpdesk_motive(self):
        return {
            "id": {"required": True, "type": "integer"},
            "name": {"type": "string", "nullable": False, "required": True},
        }
