from odoo.addons.component.core import Component


class ShopfloorApp(Component):
    """Generic endpoints for the Application."""

    _inherit = "base.shopfloor.service"
    _name = "shopfloor.app"
    _usage = "app"
    _description = __doc__

    def user_config(self):
        menu_comp = self.component("menu")
        profiles_comp = self.component("profile")
        menus = menu_comp._to_json(menu_comp._search())
        profiles = profiles_comp._to_json(profiles_comp._search())
        return self._response(data={"menus": menus, "profiles": profiles})


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
        menu_return_validator = self.component("menu.validator.response")
        profile_return_validator = self.component("profile.validator.response")
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
                "profiles": {
                    "type": "list",
                    "required": True,
                    "schema": {
                        "type": "dict",
                        "schema": profile_return_validator._record_schema,
                    },
                },
            }
        )
