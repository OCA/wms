from odoo import fields
from odoo.addons.component.core import Component

from odoo.addons.base_rest.components.service import to_int


class ShopfloorDevice(Component):
    _inherit = "base.shopfloor.service"
    _name = "shopfloor.device"
    _usage = "device"
    _expose_model = "shopfloor.device"

    def search(self, name_fragment=None):
        domain = self._get_base_search_domain()
        if name_fragment:
            domain.append(("name", "ilike", name_fragment))
        records = self.env[self._expose_model].search(domain)
        return {"size": len(records), "data": self._to_json(records)}

    def _get_base_search_domain(self):
        # shopfloor_device_ids is a one2one
        user = self.env.user
        assigned_device = fields.first(user.shopfloor_device_ids)
        if assigned_device:
            return [("id", "=", assigned_device.id)]
        return [
            "|",
            ("operation_group_ids", "=", False),
            ("operation_group_ids.user_ids", "=", user.id),
        ]

    def _validator_search(self):
        return {
            "name_fragment": {
                "type": "string",
                "nullable": True,
                "required": False,
            }
        }

    def _validator_return_search(self):
        return {
            "size": {"coerce": to_int, "required": True, "type": "integer"},
            "data": {
                "type": "list",
                "schema": {
                    "type": "dict",
                    "schema": {
                        "id": {"coerce": to_int, "required": True, "type": "integer"},
                        "name": {"type": "string", "nullable": False, "required": True},
                        "warehouse": {
                            "type": "dict",
                            "schema": {
                                "id": {"coerce": to_int, "required": True, "type": "integer"},
                                "name": {"type": "string", "nullable": False, "required": True},
                            }
                        }
                    }
                }
            }
        }

    def _convert_one_record(self, record):
        return {
            "id": record.id,
            "name": record.name,
            "warehouse": {
                "id": record.warehouse_id.id,
                "name": record.warehouse_id.name,
            }
        }
