from odoo import fields
from odoo.osv import expression

from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import Component


class ShopfloorProfile(Component):
    """
    Profile storing the configuration for the interaction from the client.

    A client application must use a profile, passed to every request in the
    HTTP header (TODO put the name of the header).

    The list of profiles available for a user is restricted by 2 things:

    * If the profile has operation groups, the profile can be used only
      if the user is at least in one of these groups.
    * If the user has an assigned profile, the user can use only this profile.
    """

    _inherit = "base.shopfloor.service"
    _name = "shopfloor.profile"
    _usage = "profile"
    _expose_model = "shopfloor.profile"
    _description = __doc__

    def search(self, name_fragment=None):
        """List available profiles for current user"""
        domain = self._get_base_search_domain()
        if name_fragment:
            domain.append(("name", "ilike", name_fragment))
        records = self.env[self._expose_model].search(domain)
        return {"data": {"size": len(records), "records": self._to_json(records)}}

    def _get_base_search_domain(self):
        # shopfloor_profile_ids is a one2one in practice.
        base_domain = super()._get_base_search_domain()
        user = self.env.user
        assigned_profile = fields.first(user.shopfloor_profile_ids)
        if assigned_profile:
            return expression.AND([base_domain, [("id", "=", assigned_profile.id)]])

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

    def _validator_search(self):
        return {
            "name_fragment": {"type": "string", "nullable": True, "required": False}
        }

    def _validator_return_search(self):
        return self._response_schema(
            {
                "size": {"coerce": to_int, "required": True, "type": "integer"},
                "records": {
                    "type": "list",
                    "schema": {
                        "type": "dict",
                        "schema": {
                            "id": {
                                "coerce": to_int,
                                "required": True,
                                "type": "integer",
                            },
                            "name": {
                                "type": "string",
                                "nullable": False,
                                "required": True,
                            },
                            "warehouse": {
                                "type": "dict",
                                "schema": {
                                    "id": {
                                        "coerce": to_int,
                                        "required": True,
                                        "type": "integer",
                                    },
                                    "name": {
                                        "type": "string",
                                        "nullable": False,
                                        "required": True,
                                    },
                                },
                            },
                        },
                    },
                },
            }
        )

    def _convert_one_record(self, record):
        return {
            "id": record.id,
            "name": record.name,
            "warehouse": {
                "id": record.warehouse_id.id,
                "name": record.warehouse_id.name,
            },
        }
