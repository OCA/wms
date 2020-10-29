# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from .common import CommonCase


class AppCase(CommonCase):
    @classmethod
    def setUpClassVars(cls, *args, **kwargs):
        super().setUpClassVars(*args, **kwargs)
        cls.profile = cls.env.ref("shopfloor.shopfloor_profile_hb_truck_demo")
        cls.profile2 = cls.env.ref("shopfloor.shopfloor_profile_shelf_1_demo")

    def setUp(self):
        super().setUp()
        with self.work_on_services(profile=self.profile) as work:
            self.service = work.component(usage="app")

    def test_user_config(self):
        """Request /app/user_config"""
        # Simulate the client asking the configuration
        response = self.service.dispatch("user_config")
        profiles = self.env["shopfloor.profile"].search([])
        self.assert_response(
            response,
            data={
                "profiles": [
                    {
                        "id": profile.id,
                        "name": profile.name,
                        "warehouse": {
                            "id": profile.warehouse_id.id,
                            "name": profile.warehouse_id.name,
                        },
                    }
                    for profile in profiles
                ],
            },
        )
