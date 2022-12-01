# Copyright 2022 Brian McMaster <brian@mcmpest.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo.addons.shopfloor_base.tests.common import CommonCase


class TestDefaultProfileCase(CommonCase):
    @classmethod
    def setUpShopfloorApp(cls):
        super().setUpShopfloorApp()
        # Enable default profile for shopfloor app
        cls.shopfloor_app.sudo().write(
            {
                "use_default_profile": True,
            }
        )
        # Add a default profile value to the user
        cls.shopfloor_user.shopfloor_default_profile_ids = [
            (0, 0, cls._user_default_profile_values())
        ]

    @classmethod
    def _user_default_profile_values(cls):
        return {
            "shopfloor_app_id": cls.shopfloor_app.id,
            "profile_id": cls.env.ref("shopfloor_base.profile_demo_2").id,
        }

    def test_make_app_info_default_profile(self):
        info = self.shopfloor_app._make_app_info()
        self.assertTrue(info["use_default_profile"])

    def test_user_info_default_profile(self):
        """Request /user/user_info"""
        service = self.get_service("user")
        response = service.dispatch("user_info")
        self.assert_response(
            response,
            data={
                "user_info": {
                    "id": self.env.user.id,
                    "name": self.env.user.name,
                    "lang": self.env.user.lang.replace("_", "-"),
                    "default_profile": {
                        "id": self.env.ref("shopfloor_base.profile_demo_2").id,
                        "name": self.env.ref("shopfloor_base.profile_demo_2").name,
                    },
                }
            },
        )
