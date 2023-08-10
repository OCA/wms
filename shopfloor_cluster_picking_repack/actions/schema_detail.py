# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class ShopfloorSchemaDetailAction(Component):
    _inherit = "shopfloor.schema.detail.action"

    def pack_picking_detail(self):
        schema = {
            "id": {"required": True, "type": "integer"},
            "name": {"type": "string", "required": True, "nullable": False},
            "partner": {
                "type": "dict",
                "required": True,
                "nullable": False,
                "schema": {
                    "id": {"required": True, "type": "integer"},
                    "name": {"type": "string", "required": True, "nullable": False},
                },
            },
            "scanned_packs": {"type": "list", "schema": {"type": "integer"}},
            "move_lines": {
                "type": "list",
                "schema": {
                    "type": "dict",
                    "schema": {
                        "id": {"required": True, "type": "integer"},
                        "qty_done": {"type": "float", "required": True},
                        "lot": {
                            "type": "dict",
                            "required": False,
                            "nullable": True,
                            "schema": self.lot(),
                        },
                        "package_dest": self._schema_dict_of(
                            self.package(with_packaging=False), required=False
                        ),
                        "package_src": self._schema_dict_of(
                            self.package(with_packaging=False), required=False
                        ),
                        "product": self._schema_dict_of(self.product()),
                    },
                },
            },
        }
        return schema
