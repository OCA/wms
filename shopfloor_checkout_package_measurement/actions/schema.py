# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
from odoo.addons.component.core import Component


class ShopfloorSchemaAction(Component):
    _inherit = "shopfloor.schema.action"

    def package(self, with_packaging=False):
        res = super().package(with_packaging=with_packaging)
        res.update(
            {
                "height": {"required": False, "nullable": True, "type": "float"},
                "length": {"required": False, "nullable": True, "type": "float"},
                "width": {"required": False, "nullable": True, "type": "float"},
                "shipping_weight": {
                    "required": False,
                    "nullable": True,
                    "type": "float",
                },
                "dimension_uom": self._schema_dict_of(
                    self._simple_record(), required=False
                ),
                "weight_uom": self._schema_dict_of(
                    self._simple_record(), required=False
                ),
            }
        )
        return res

    def package_requirement(self):
        return {
            "height": {"required": False, "nullable": True, "type": "boolean"},
            "length": {"required": False, "nullable": True, "type": "boolean"},
            "width": {"required": False, "nullable": True, "type": "boolean"},
            "shipping_weight": {"required": False, "nullable": True, "type": "boolean"},
        }
