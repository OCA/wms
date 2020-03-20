from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import Component


class ShopfloorPack(Component):
    """Expose data about Stock Quant Packages"""

    _inherit = "base.shopfloor.service"
    _name = "shopfloor.pack"
    _usage = "pack"
    _description = __doc__

    def get_by_name(self, pack_name):
        """Get pack information"""
        search = self.actions_for("search")
        package = search.package_from_scan(pack_name)
        return self._response(data=self._to_json(package)[:1])

    def _convert_one_record(self, record):
        return {
            "id": record.id,
            "name": record.name,
            "location": {"id": record.location_id.id, "name": record.location_id.name},
        }


class ShopfloorPackValidator(Component):
    """Validators for the Pack endpoints"""

    _inherit = "base.shopfloor.validator"
    _name = "shopfloor.pack.validator"
    _usage = "pack.validator"

    def get_by_name(self):
        return {"pack_name": {"type": "string", "nullable": False, "required": True}}


class ShopfloorPackValidatorResponse(Component):
    """Validators for the Pack endpoints responses"""

    _inherit = "base.shopfloor.validator.response"
    _name = "shopfloor.pack.validator.response"
    _usage = "pack.validator.response"

    @property
    def _record_schema(self):
        return {
            "id": {"coerce": to_int, "required": True, "type": "integer"},
            "name": {"type": "string", "nullable": False, "required": True},
            "location": {
                "type": "dict",
                "schema": {
                    "id": {"coerce": to_int, "required": True, "type": "integer"},
                    "name": {"type": "string", "nullable": False, "required": True},
                },
            },
        }

    def get_by_name(self):
        return self._response_schema(self._record_schema)
