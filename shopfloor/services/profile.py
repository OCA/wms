# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import Component


class ShopfloorProfile(Component):
    """
    Profile storing the configuration for the interaction from the client.

    A client application must use a profile, passed to every request in the
    HTTP header HTTP_SERVICE_CTX_PROFILE_ID.

    Only stock managers should be allowed to change the profile for a device.
    """

    _inherit = "base.shopfloor.service"
    _name = "shopfloor.profile"
    _usage = "profile"
    _expose_model = "shopfloor.profile"
    _description = __doc__

    def _search(self, name_fragment=None):
        domain = self._get_base_search_domain()
        if name_fragment:
            domain.append(("name", "ilike", name_fragment))
        records = self.env[self._expose_model].search(domain)
        return records

    def search(self, name_fragment=None):
        """List available profiles"""
        records = self._search(name_fragment=name_fragment)
        return self._response(
            data={"size": len(records), "records": self._to_json(records)}
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


class ShopfloorProfileValidator(Component):
    """Validators for the Profile endpoints"""

    _inherit = "base.shopfloor.validator"
    _name = "shopfloor.profile.validator"
    _usage = "profile.validator"

    def search(self):
        return {
            "name_fragment": {"type": "string", "nullable": True, "required": False}
        }


class ShopfloorProfileValidatorResponse(Component):
    """Validators for the Profile endpoints responses"""

    _inherit = "base.shopfloor.validator.response"
    _name = "shopfloor.profile.validator.response"
    _usage = "profile.validator.response"

    def search(self):
        return self._response_schema(
            {
                "size": {"coerce": to_int, "required": True, "type": "integer"},
                "records": {
                    "type": "list",
                    "schema": {"type": "dict", "schema": self._record_schema},
                },
            }
        )

    @property
    def _record_schema(self):
        return {
            "id": {"coerce": to_int, "required": True, "type": "integer"},
            "name": {"type": "string", "nullable": False, "required": True},
            "warehouse": {
                "type": "dict",
                "schema": {
                    "id": {"coerce": to_int, "required": True, "type": "integer"},
                    "name": {"type": "string", "nullable": False, "required": True},
                },
            },
        }
