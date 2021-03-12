# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
from odoo.addons.component.core import Component


class ShopfloorApp(Component):
    """Generic endpoints for the Application."""

    _inherit = "base.shopfloor.service"
    _name = "shopfloor.app"
    _usage = "app"
    _description = __doc__

    # TODO: maybe rename to `config` or `app_config`
    # as this is not related to current user conf
    def user_config(self):
        profiles_comp = self.component("profile")
        profiles = profiles_comp._to_json(profiles_comp._search())
        user_comp = self.component("user")
        user_info = user_comp._user_info()
        return self._response(data={"profiles": profiles, "user_info": user_info})


class ShopfloorAppValidator(Component):
    """Validators for the Application endpoints"""

    _inherit = "base.shopfloor.validator"
    _name = "shopfloor.app.validator"
    _usage = "app.validator"

    def user_config(self):
        return {}


class ShopfloorAppValidatorResponse(Component):
    """Validators for the Application endpoints responses"""

    _inherit = "base.shopfloor.validator.response"
    _name = "shopfloor.app.validator.response"
    _usage = "app.validator.response"

    def user_config(self):
        profile_return_validator = self.component("profile.validator.response")
        user_return_validator = self.component("user.validator.response")
        return self._response_schema(
            {
                "profiles": {
                    "type": "list",
                    "required": True,
                    "schema": {
                        "type": "dict",
                        "schema": profile_return_validator._record_schema,
                    },
                },
                "user_info": {
                    "type": "dict",
                    "required": True,
                    "schema": user_return_validator._user_info_schema(),
                },
            }
        )
