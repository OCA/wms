from odoo.addons.component.core import Component


class ShopfloorDevice(Component):
    _inherit = "base.shopfloor.service"
    _name = "shopfloor.device"
    _usage = "device"
    _expose_model = "shopfloor.device"

    def search(self, name_fragment=None):
        # TODO filter on shopfloor.group or user in override of _get_base_search_domain
        domain = self._get_base_search_domain()
        if name_fragment:
            domain.append(("name", "ilike", name_fragment))
        records = self.env[self._expose_model].search(domain)
        return {"size": len(records), "data": self._to_json(records)}

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
