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

    def lot(self):
        res = super().lot()

        # We need to be able to send lot name and expiration date info
        # for "virtual lot" not yet created -> not yet an id
        res.update(
            {
                "id": {"required": False, "type": "integer"},
            }
        )
        return res
