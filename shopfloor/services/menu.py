from odoo.osv import expression

from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import Component


class ShopfloorMenu(Component):
    """
    Menu Structure for the client application.

    The list of menus is restricted by the operation groups. A menu without
    groups is visible for all users, a menu with group(s) is visible if the
    user is in at least one of the groups.
    """

    _inherit = "base.shopfloor.service"
    _name = "shopfloor.menu"
    _usage = "menu"
    _expose_model = "shopfloor.menu"
    _description = __doc__

    def _get_base_search_domain(self):
        base_domain = super()._get_base_search_domain()
        user = self.env.user
        return expression.AND(
            [
                base_domain,
                [
                    "|",
                    ("operation_group_ids", "=", False),
                    ("operation_group_ids.user_ids", "=", user.id),
                ],
            ]
        )

    def _search(self, name_fragment=None):
        domain = self._get_base_search_domain()
        if name_fragment:
            domain.append(("name", "ilike", name_fragment))
        records = self.env[self._expose_model].search(domain)
        return records

    def search(self, name_fragment=None):
        """List available menu entries for current user"""
        records = self._search(name_fragment=name_fragment)
        return self._response(
            data={"size": len(records), "records": self._to_json(records)}
        )

    def _convert_one_record(self, record):
        return {
            "id": record.id,
            "name": record.name,
            "process": {"id": record.process_id.id, "code": record.process_code},
        }


class ShopfloorMenuValidator(Component):
    """Validators for the Menu endpoints"""

    _inherit = "base.shopfloor.validator"
    _name = "shopfloor.menu.validator"
    _usage = "menu.validator"

    def search(self):
        return {
            "name_fragment": {"type": "string", "nullable": True, "required": False}
        }


class ShopfloorMenuValidatorResponse(Component):
    """Validators for the Menu endpoints responses"""

    _inherit = "base.shopfloor.validator.response"
    _name = "shopfloor.menu.validator.response"
    _usage = "menu.validator.response"

    @property
    def _record_schema(self):
        return {
            "id": {"coerce": to_int, "required": True, "type": "integer"},
            "name": {"type": "string", "nullable": False, "required": True},
            "process": {
                "type": "dict",
                "required": True,
                "schema": {
                    "code": {"type": "string", "nullable": False, "required": True},
                    "id": {"coerce": to_int, "required": True, "type": "integer"},
                },
            },
        }

    def return_search(self):
        return self._response_schema(
            {
                "size": {"coerce": to_int, "required": True, "type": "integer"},
                "records": {
                    "type": "list",
                    "required": True,
                    "schema": {"type": "dict", "schema": self._record_schema},
                },
            }
        )
