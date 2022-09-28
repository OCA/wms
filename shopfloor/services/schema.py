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

    def _simple_record(self):
        return {
            "id": {"required": True, "type": "integer"},
            "name": {"type": "string", "nullable": False, "required": True},
        }

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
        }

    def move_line(self, with_packaging=False):
        return {
            "id": {"type": "integer", "required": True},
            "qty_done": {"type": "float", "required": True},
            "quantity": {"type": "float", "required": True},
            "product": {"type": "dict", "required": True, "schema": self.product()},
            "lot": {
                "type": "dict",
                "required": False,
                "nullable": True,
                "schema": self.lot(),
            },
            "package_src": {
                "type": "dict",
                "required": True,
                "nullable": True,
                "schema": self.package(with_packaging=with_packaging),
            },
            "package_dest": {
                "type": "dict",
                "required": False,
                "nullable": True,
                "schema": self.package(with_packaging=with_packaging),
            },
            "location_src": {
                "type": "dict",
                "required": True,
                "schema": self.location(),
            },
            "location_dest": {
                "type": "dict",
                "required": True,
                "schema": self.location(),
            },
        }

    def product(self):
        return {
            "id": {"required": True, "type": "integer"},
            "name": {"type": "string", "nullable": False, "required": True},
            "display_name": {"type": "string", "nullable": False, "required": True},
            "default_code": {"type": "string", "nullable": False, "required": True},
            "barcode": {"type": "string", "nullable": True, "required": False},
            "packaging": self._schema_list_of(self.packaging()),
        }

    def package(self, with_packaging=False):
        schema = {
            "id": {"required": True, "type": "integer"},
            "name": {"type": "string", "nullable": False, "required": True},
            "weight": {"required": True, "nullable": True, "type": "float"},
            "move_line_count": {"required": False, "nullable": True, "type": "integer"},
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
            "name": {"type": "string", "nullable": False, "required": True},
            "location_src": {"type": "dict", "schema": self.location()},
            "location_dest": {"type": "dict", "schema": self.location()},
            "product": {"type": "dict", "schema": self.product()},
            "picking": {"type": "dict", "schema": self.picking()},
        }
