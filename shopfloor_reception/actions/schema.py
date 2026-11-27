# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.addons.component.core import Component


class ShopfloorSchemaAction(Component):
    _inherit = "shopfloor.schema.action"

    def product(self):
        res = super().product()
        res.update(
            {
                "use_expiration_date": {
                    "type": "boolean",
                    "nullable": True,
                    "required": False,
                },
            }
        )
        return res

    def lot_suggestion(self):
        """Schema used to suggest a lot payload before creation.

        All attributes are optional so the client can progressively complete
        values before sending a final payload for lot creation.
        """
        res = super().lot()
        for _field, spec in res.items():
            if isinstance(spec, dict):
                spec["required"] = False
                spec.setdefault("nullable", True)
        return res
