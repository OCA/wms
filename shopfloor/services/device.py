from odoo import fields
from odoo.addons.component.core import Component

from odoo.addons.base_rest.components.service import skip_secure_response


class ShopfloorDevice(Component):
    _inherit = "base.shopfloor.service"
    _name = "shopfloor.device"
    _usage = "device"
    _expose_model = "shopfloor.device"

    @skip_secure_response
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

    def _convert_one_record(self, record):
        return {
            "id": record.id,
            "name": record.name,
            "warehouse_id": record.warehouse_id.id,
            "warehouse": record.warehouse_id.name,
        }
