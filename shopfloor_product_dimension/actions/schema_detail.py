# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.addons.component.core import Component


class ShopfloorSchemaDetailAction(Component):
    _inherit = "shopfloor.schema.detail.action"

    def product_detail(self):
        schema = super().product_detail()
        schema.update(
            {
                "length": {"type": "float", "nullable": True, "required": False},
                "width": {"type": "float", "nullable": True, "required": False},
                "height": {"type": "float", "nullable": True, "required": False},
                "weight": {"type": "float", "nullable": True, "required": False},
                "dimension_uom": self._schema_dict_of(
                    self._simple_record(
                        factor={"required": True, "nullable": True, "type": "float"},
                        rounding={"required": True, "nullable": True, "type": "float"},
                    )
                ),
                "weight_uom": self._schema_dict_of(
                    self._simple_record(
                        factor={"required": True, "nullable": True, "type": "float"},
                        rounding={"required": True, "nullable": True, "type": "float"},
                    )
                ),
            }
        )
        return schema
