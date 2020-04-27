from .common import CommonCase


class AppCase(CommonCase):
    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)
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

    def test_menu_no_profile(self):
        """Request /app/menu"""
        # Simulate the client asking the menu
        response = self.service.dispatch("menu")
        menus = self.env["shopfloor.menu"].search([])
        self.assert_response(
            response,
            data={
                "menus": [
                    {
                        "id": menu.id,
                        "name": menu.name,
                        "scenario": menu.scenario,
                        "picking_types": [
                            {"id": picking_type.id, "name": picking_type.name}
                            for picking_type in menu.picking_type_ids
                        ],
                    }
                    for menu in menus
                ]
            },
        )

    def test_menu_by_profile(self):
        """Request /app/menu w/ a specific profile"""
        # Simulate the client asking the menu
        menus = self.env["shopfloor.menu"].search([])
        menu = menus[0]
        menu.profile_ids = self.profile
        (menus - menu).profile_ids = self.profile2

        response = self.service.dispatch("menu")
        self.assert_response(
            response,
            data={
                "menus": [
                    {
                        "id": menu.id,
                        "name": menu.name,
                        "scenario": menu.scenario,
                        "picking_types": [
                            {"id": picking_type.id, "name": picking_type.name}
                            for picking_type in menu.picking_type_ids
                        ],
                    }
                ]
            },
        )
