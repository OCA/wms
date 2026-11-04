# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.addons.component.core import Component


class ShopfloorMenu(Component):
    _inherit = "shopfloor.service.menu"

    def _one_record_parser(self, record):
        parser = super()._one_record_parser(record)
        return parser + ["allow_quantity_exceeding_demand"]


class ShopfloorMenuValidatorResponse(Component):
    _inherit = "shopfloor.service.menu.validator.response"

    @property
    def _record_schema(self):
        schema = super()._record_schema
        schema.update(
            {
                "allow_quantity_exceeding_demand": {
                    "type": "boolean",
                    "nullable": True,
                    "required": False,
                }
            }
        )
        return schema
