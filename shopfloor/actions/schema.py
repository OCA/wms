# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.addons.component.core import Component


class ShopfloorSchemaAction(Component):

    _inherit = "shopfloor.schema.action"

    def picking(self):
        return {
            "id": {"required": True, "type": "integer"},
            "name": {"type": "string", "nullable": False, "required": True},
            "origin": {"type": "string", "nullable": True, "required": False},
            "note": {"type": "string", "nullable": True, "required": False},
            "move_line_count": {"type": "integer", "nullable": True, "required": True},
            "package_level_count": {
                "type": "integer",
                "nullable": True,
                "required": True,
            },
            "bulk_line_count": {"type": "integer", "nullable": True, "required": True},
            "weight": {"required": True, "nullable": True, "type": "float"},
            "partner": self._schema_dict_of(self._simple_record()),
            "carrier": self._schema_dict_of(self._simple_record(), required=False),
            "ship_carrier": self._schema_dict_of(self._simple_record(), required=False),
            "scheduled_date": {"type": "string", "nullable": False, "required": True},
        }

    def move_line(self, with_packaging=False, with_picking=False):
        schema = {
            "id": {"type": "integer", "required": True},
            "qty_done": {"type": "float", "required": True},
            "quantity": {"type": "float", "required": True},
            "product": self._schema_dict_of(self.product()),
            "lot": {
                "type": "dict",
                "required": False,
                "nullable": True,
                "schema": self.lot(),
            },
            "package_src": self._schema_dict_of(
                self.package(with_packaging=with_packaging)
            ),
            "package_dest": self._schema_dict_of(
                self.package(with_packaging=with_packaging), required=False
            ),
            "location_src": self._schema_dict_of(self.location()),
            "location_dest": self._schema_dict_of(self.location()),
            "priority": {"type": "string", "nullable": True, "required": False},
        }
        if with_picking:
            schema["picking"] = self._schema_dict_of(self.picking())
        return schema

    def move(self):
        return {
            "id": {"required": True, "type": "integer"},
            "priority": {"type": "string", "required": False, "nullable": True},
        }

    def product(self):
        return {
            "id": {"required": True, "type": "integer"},
            "name": {"type": "string", "nullable": False, "required": True},
            "display_name": {"type": "string", "nullable": False, "required": True},
            "default_code": {"type": "string", "nullable": True, "required": True},
            "barcode": {"type": "string", "nullable": True, "required": False},
            "supplier_code": {"type": "string", "nullable": True, "required": False},
            "packaging": self._schema_list_of(self.packaging()),
            "uom": self._schema_dict_of(
                self._simple_record(
                    factor={"required": True, "nullable": True, "type": "float"},
                    rounding={"required": True, "nullable": True, "type": "float"},
                )
            ),
        }

    def package(self, with_packaging=False):
        schema = {
            "id": {"required": True, "type": "integer"},
            "name": {"type": "string", "nullable": False, "required": True},
            "weight": {"required": True, "nullable": True, "type": "float"},
            "move_line_count": {"required": False, "nullable": True, "type": "integer"},
            "storage_type": self._schema_dict_of(self._simple_record()),
        }
        if with_packaging:
            schema["packaging"] = self._schema_dict_of(self.packaging())
        return schema

    def lot(self):
        return {
            "id": {"required": True, "type": "integer"},
            "name": {"type": "string", "nullable": False, "required": True},
            "ref": {"type": "string", "nullable": True, "required": False},
        }

    def location(self):
        return {
            "id": {"required": True, "type": "integer"},
            "name": {"type": "string", "nullable": False, "required": True},
            "barcode": {"type": "string", "nullable": True, "required": False},
        }

    def packaging(self):
        return {
            "id": {"required": True, "type": "integer"},
            "name": {"type": "string", "nullable": False, "required": True},
            "code": {"type": "string", "nullable": True, "required": True},
            "qty": {"type": "float", "required": True},
        }

    def delivery_packaging(self):
        return {
            "id": {"required": True, "type": "integer"},
            "name": {"type": "string", "nullable": False, "required": True},
            "packaging_type": {"type": "string", "nullable": True, "required": True},
            "barcode": {"type": "string", "nullable": True, "required": True},
        }

    def picking_batch(self, with_pickings=False):
        schema = {
            "id": {"required": True, "type": "integer"},
            "name": {"type": "string", "nullable": False, "required": True},
            "picking_count": {"required": True, "type": "integer"},
            "move_line_count": {"required": True, "type": "integer"},
            "weight": {"required": True, "nullable": True, "type": "float"},
        }
        if with_pickings:
            schema["pickings"] = self._schema_list_of(self.picking())
        return schema

    def package_level(self):
        return {
            "id": {"required": True, "type": "integer"},
            "is_done": {"type": "boolean", "nullable": False, "required": True},
            "picking": self._schema_dict_of(self._simple_record()),
            "package_src": self._schema_dict_of(self.package()),
            "location_src": self._schema_dict_of(self.location()),
            "location_dest": self._schema_dict_of(self.location()),
            "product": self._schema_dict_of(self.product()),
            "quantity": {"type": "float", "required": True},
        }

    def picking_type(self):
        return {
            "id": {"required": True, "type": "integer"},
            "name": {"type": "string", "nullable": False, "required": True},
        }

    def move_lines_counters(self):
        return {
            "lines_count": {"type": "float", "required": False, "nullable": True},
            "picking_count": {"type": "float", "required": False, "nullable": True},
            "priority_lines_count": {
                "type": "float",
                "required": False,
                "nullable": True,
            },
            "priority_picking_count": {
                "type": "float",
                "required": False,
                "nullable": True,
            },
        }

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
