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
        profile = getattr(self.work, "profile", None)
        op_group_domain = [
            "|",
            ("operation_group_ids", "=", False),
            ("operation_group_ids.user_ids", "=", user.id),
        ]
        if profile:
            # TODO: this probably should be the default only one way
            # What to do w/ profiles linked to specific user?
            # This data model is a bit messy :/
            op_group_domain = [
                ("operation_group_ids", "in", profile.operation_group_ids.ids),
            ]
        return expression.AND([base_domain, op_group_domain])

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
        # TODO: use `jsonify`
        return {
            "id": record.id,
            "name": record.name,
            "process": {
                "id": record.process_id.id,
                "code": record.process_code,
                "picking_type": {
                    "id": record.process_id.picking_type_id.id,
                    "name": record.process_id.picking_type_id.name,
                },
            },
            "op_groups": [
                {"id": g.id, "name": g.name} for g in record.operation_group_ids
            ],
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

    @property
    def _record_schema(self):
        return {
            "id": {"coerce": to_int, "required": True, "type": "integer"},
            "name": {"type": "string", "nullable": False, "required": True},
            "op_groups": {
                "type": "list",
                "required": True,
                "schema": {"type": "dict", "schema": self._op_group_schema},
            },
            "process": {
                "type": "dict",
                "required": True,
                "schema": {
                    "id": {"coerce": to_int, "required": True, "type": "integer"},
                    "code": {"type": "string", "nullable": False, "required": True},
                    "picking_type": {
                        "type": "dict",
                        "schema": self._picking_type_schema,
                    },
                },
            },
        }

    @property
    def _op_group_schema(self):
        return {
            "id": {"coerce": to_int, "required": True, "type": "integer"},
            "name": {"type": "string", "nullable": False, "required": True},
        }

    @property
    def _picking_type_schema(self):
        return {
            "id": {"coerce": to_int, "required": True, "type": "integer"},
            "name": {"type": "string", "nullable": False, "required": True},
        }
