# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import Component


class ShopfloorUser(Component):
    """Generic endpoints for user specific info."""

    _inherit = "base.shopfloor.service"
    _name = "shopfloor.user"
    _usage = "user"
    _description = __doc__
    _requires_header_profile = True

    def menu(self):
        menu_comp = self.component("menu")
        menus = menu_comp._to_json(menu_comp._search())
        return self._response(data={"menus": menus})

    # TODO: this endpoint does not require profile header
    def user_info(self):
        return self._response(data={"user_info": self._user_info()})

    def _user_info(self):
        return self.env.user.jsonify(self._user_info_parser, one=True)

    @property
    def _user_info_parser(self):
        return ["id", "name"]


class ShopfloorUserValidator(Component):
    """Validators for the User endpoints"""

    _inherit = "base.shopfloor.validator"
    _name = "shopfloor.user.validator"
    _usage = "user.validator"

    def menu(self):
        return {}

    def user_info(self):
        return {}


class ShopfloorUserValidatorResponse(Component):
    """Validators for the User endpoints responses"""

    _inherit = "base.shopfloor.validator.response"
    _name = "shopfloor.user.validator.response"
    _usage = "user.validator.response"

    def menu(self):
        menu_return_validator = self.component("menu.validator.response")
        return self._response_schema(
            {
                "menus": {
                    "type": "list",
                    "required": True,
                    "schema": {
                        "type": "dict",
                        "schema": menu_return_validator._record_schema,
                    },
                },
            }
        )

    def user_info(self):
        return self._response_schema(
            {
                "user_info": {
                    "type": "dict",
                    "required": True,
                    "schema": self._user_info_schema(),
                }
            }
        )

    def _user_info_schema(self):
        return {
            "id": {"coerce": to_int, "required": True, "type": "integer"},
            "name": {"type": "string", "nullable": False, "required": True},
        }
