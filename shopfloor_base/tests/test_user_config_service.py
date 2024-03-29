# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
from .common import CommonCase


class AppCase(CommonCase):
    @classmethod
    def setUpClassVars(cls):
        super().setUpClassVars()
        cls.profile = cls.env.ref("shopfloor_base.profile_demo_1")
        cls.profile2 = cls.env.ref("shopfloor_base.profile_demo_2")
        return

    def test_user_config(self):
        """Request /app/user_config"""
        # Simulate the client asking the configuration
        service = self.get_service("app", profile=self.profile)
        response = service.dispatch("user_config")
        profiles = self.env["shopfloor.profile"].search([])
        self.assert_response(
            response,
            data={
                "profiles": [
                    {"id": profile.id, "name": profile.name} for profile in profiles
                ],
                "user_info": {
                    "id": self.env.user.id,
                    "name": self.env.user.name,
                    "lang": self.env.user.lang.replace("_", "-"),
                },
            },
        )
