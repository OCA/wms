from .common import CommonCase


class AppCase(CommonCase):
    def setUp(self):
        super().setUp()
        with self.work_on_services() as work:
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
                        "process": {
                            "id": menu.process_id.id,
                            "code": menu.process_id.code,
                        },
                    }
                    for menu in menus
                ],
            },
        )

    def test_menu_by_profile(self):
        """Request /app/menu w/ a specific profile"""
        # Simulate the client asking the menu
        op_type = self.env.ref("shopfloor.shopfloor_operation_group_highbay_demo")
        menus = self.env["shopfloor.menu"].search([])
        menu = menus[0]
        menu.operation_group_ids = op_type
        profile = self.env.ref("shopfloor.shopfloor_profile_hb_truck_demo")
        profile.operation_group_ids = op_type

        with self.work_on_services(profile=profile) as work:
            service = work.component(usage="app")

        response = service.dispatch("menu")
        self.assert_response(
            response,
            data={
                "menus": [
                    {
                        "id": menu.id,
                        "name": menu.name,
                        "process": {
                            "id": menu.process_id.id,
                            "code": menu.process_id.code,
                        },
                    }
                ],
            },
        )
