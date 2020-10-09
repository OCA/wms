# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.addons.component.core import Component


class BaseShopfloorSchemaResponse(Component):
    """Provide methods to share schema structures

    The methods should be used in Service Components, so we try to
    have similar schema structures across scenarios.
    """

    _inherit = "base.rest.service"
    _name = "base.shopfloor.schemas"
    _collection = "shopfloor.service"
    _usage = "schema"
    _is_rest_service_component = False

    def _schema_list_of(self, schema, **kw):
        schema = {
            "type": "list",
            "nullable": True,
            "required": True,
            "schema": {"type": "dict", "schema": schema},
        }
        schema.update(kw)
        return schema

    def _simple_record(self, **kw):
        schema = {
            "id": {"required": True, "type": "integer"},
            "name": {"type": "string", "nullable": False, "required": True},
        }
        schema.update(kw)
        return schema

    def _schema_dict_of(self, schema, **kw):
        schema = {
            "type": "dict",
            "nullable": True,
            "required": True,
            "schema": schema,
        }
        schema.update(kw)
        return schema

    def _schema_search_results_of(self, schema, **kw):
        return {
            "size": {"required": True, "type": "integer"},
            "records": {
                "type": "list",
                "required": True,
                "schema": {"type": "dict", "schema": schema},
            },
        }

    def picking(self):
        return {
            "id": {"required": True, "type": "integer"},
            "name": {"type": "string", "nullable": False, "required": True},
            "origin": {"type": "string", "nullable": True, "required": False},
            "note": {"type": "string", "nullable": True, "required": False},
            "move_line_count": {"type": "integer", "nullable": True, "required": True},
            "weight": {"required": True, "nullable": True, "type": "float"},
            "partner": {
                "type": "dict",
                "nullable": True,
                "required": True,
                "schema": {
                    "id": {"required": True, "type": "integer"},
                    "name": {"type": "string", "nullable": False, "required": True},
                },
            },
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
