# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
from odoo.osv import expression

from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import Component


class ShopfloorMenu(Component):
    """
    Menu Structure for the client application.

    The list of menus is restricted by the profiles.
    A menu without profile is shown in every profiles.
    """

    _inherit = "base.shopfloor.service"
    _name = "shopfloor.menu"
    _usage = "menu"
    _expose_model = "shopfloor.menu"
    _description = __doc__

    def _get_base_search_domain(self):
        base_domain = super()._get_base_search_domain()
        return expression.AND(
            [
                base_domain,
                [
                    "|",
                    ("profile_id", "=", False),
                    ("profile_id", "=", self.work.profile.id),
                ],
            ]
        )

    def _search(self, name_fragment=None):
        if not self.work.profile:
            # we need to know the profile to load menus
            return self.env["shopfloor.menu"].browse()
        domain = self._get_base_search_domain()
        if name_fragment:
            domain.append(("name", "ilike", name_fragment))
        records = self.env[self._expose_model].search(domain)
        return records

    def search(self, name_fragment=None):
        """List available menu entries for current profile"""
        records = self._search(name_fragment=name_fragment)
        return self._response(
            data={"size": len(records), "records": self._to_json(records)}
        )

    def _convert_one_record(self, record):
        values = record.jsonify(self._one_record_parser(record), one=True)
        return values

    def _one_record_parser(self, record):
        return [
            "id",
            "name",
            "scenario",
        ]


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
        record_schema = self._record_schema
        return self._response_schema(
            {
                "size": {"coerce": to_int, "required": True, "type": "integer"},
                "records": self.schemas._schema_list_of(record_schema),
            }
        )

    @property
    def _record_schema(self):
        schema = {
            "id": {"coerce": to_int, "required": True, "type": "integer"},
            "name": {"type": "string", "nullable": False, "required": True},
            "scenario": {"type": "string", "nullable": False, "required": True},
        }
        schema.update(self.schemas.menu_item_counters())
        return schema
