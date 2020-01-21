from odoo.addons.component.core import Component

from odoo.addons.base_rest.components.service import skip_secure_response


class ShopfloorMenu(Component):
    _inherit = "base.shopfloor.service"
    _name = "shopfloor.menu"
    _usage = "menu"
    _expose_model = "shopfloor.menu"

    @skip_secure_response
    def search(self, name_fragment=None):
        domain = self._get_base_search_domain()
        if name_fragment:
            domain.append(("name", "ilike", name_fragment))
        records = self.env[self._expose_model].search(domain)
        return {"size": len(records), "data": self._to_json(records)}

    def _get_base_search_domain(self):
        user = self.env.user
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
        }
