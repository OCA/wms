from odoo.addons.component.core import Component


class ShopfloorApp(Component):
    """Generic endpoints for the Application."""

    _inherit = "base.shopfloor.service"
    _name = "shopfloor.app"
    _usage = "app"
    _description = __doc__

    def user_config(self):
        menus = self.component("menu")._search()
        profiles = self.component("profile")._search()
        return self._response(data={"menus": menus, "profiles": profiles})

    def _validator_user_config(self):
        return {}

    def _validator_return_user_config(self):
        menu_service = self.component("menu")
        profile_service = self.component("profile")
        return self._response_schema(
            {
                "menus": {
                    "type": "list",
                    "required": True,
                    "schema": {
                        "type": "dict",
                        "schema": menu_service._record_return_schema,
                    },
                },
                "profiles": {
                    "type": "list",
                    "required": True,
                    "schema": {
                        "type": "dict",
                        "schema": profile_service._record_return_schema,
                    },
                },
            }
        )
