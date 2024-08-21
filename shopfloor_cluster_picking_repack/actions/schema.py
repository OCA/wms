# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class ShopfloorSchemaAction(Component):

    _inherit = "shopfloor.schema.action"

    def package(self, with_packaging=False):
        schema = super().package(with_packaging=with_packaging)
        schema["is_internal"] = {"required": False, "type": "boolean"}
        return schema

    def select_package(self) -> dict:
        """
        This will return the schema expected to display the action to select the
        package to put in.
        """
        schema = {
            "selected_move_lines": {
                "type": "list",
                "schema": self._schema_dict_of(self.move_line()),
            },
            "picking": self._schema_dict_of(self.picking()),
            "packing_info": {"type": "string", "nullable": True},
            "no_package_enabled": {
                "type": "boolean",
                "nullable": True,
                "required": False,
            },
            "package_allowed": {
                "type": "boolean",
                "nullable": True,
                "required": False,
            },
        }
        return schema
