# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.addons.component.core import Component


class ShopfloorSchemaAction(Component):
    _inherit = "shopfloor.schema.action"

    def product(self):
        res = super().product()
        res.update(
            {
                "package_type": self._schema_dict_of(
                    self._simple_record(
                        display_name={
                            "type": "string",
                            "nullable": False,
                            "required": True,
                        }
                    )
                ),
            }
        )
        return res
