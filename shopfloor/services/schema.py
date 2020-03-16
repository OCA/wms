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

    def picking(self):
        return {
            "id": {"required": True, "type": "integer"},
            "name": {"type": "string", "nullable": False, "required": True},
            "origin": {"type": "string", "nullable": True, "required": True},
            "note": {"type": "string", "nullable": True, "required": True},
            "line_count": {"type": "integer", "nullable": True, "required": True},
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

    def move_line(self):
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
                "schema": self.package(),
            },
            "package_dest": {
                "type": "dict",
                "required": True,
                "nullable": True,
                "schema": self.package(),
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
        }

    def package(self):
        return {
            "id": {"required": True, "type": "integer"},
            "name": {"type": "string", "nullable": False, "required": True},
            "weight": {"required": True, "nullable": True, "type": "float"},
            "line_count": {"required": True, "nullable": True, "type": "integer"},
            "package_type_name": {"required": True, "nullable": True, "type": "string"},
        }

    def lot(self):
        return {
            "id": {"required": True, "type": "integer"},
            "name": {"type": "string", "nullable": False, "required": True},
        }

    def location(self):
        return {
            "id": {"required": True, "type": "integer"},
            "name": {"type": "string", "nullable": False, "required": True},
        }

    def package_type(self):
        return {
            "id": {"required": True, "type": "integer"},
            "name": {"type": "string", "nullable": False, "required": True},
        }
