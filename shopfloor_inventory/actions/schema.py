# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.addons.component.core import Component


class ShopfloorSchemaAction(Component):

    _inherit = "shopfloor.schema.action"

    def inventory_location(self):
        return {
            "location": self._schema_dict_of(self.location()),
            "state": {"required": True, "type": "string"},
        }

    def inventory(self, with_locations=False):
        schema = {
            "id": {"required": True, "type": "integer"},
            "name": {"required": True, "type": "string"},
            "date": {"required": True, "type": "string"},
            "location_count": {"required": True, "type": "integer"},
            "remaining_location_count": {"required": True, "type": "integer"},
            "inventory_line_count": {"required": True, "type": "integer"},
        }
        if with_locations:
            schema["locations"] = self._schema_list_of(self.inventory_location())
        return schema

    def inventory_line(self):
        return {
            "id": {"required": True, "type": "integer"},
            "product_qty": {"required": True, "type": "float"},
            "theoretical_qty": {"required": True, "type": "float"},
            "product": self._schema_dict_of(self.product()),
            "lot": self._schema_dict_of(self.lot()),
            "location": self._schema_dict_of(self.location()),
            "package": self._schema_dict_of(self.package()),
        }
