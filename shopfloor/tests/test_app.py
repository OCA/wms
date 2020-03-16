from .common import CommonCase


class AppCase(CommonCase):
    def setUp(self):
        super().setUp()
        with self.work_on_services() as work:
            self.service = work.component(usage="app")

    def test_to_openapi(self):
        # will raise if it fails to generate the openapi specs
        self.service.to_openapi()

    def test_user_config(self):
        """Request /app/user_config"""
        # Simulate the client asking the configuration
        response = self.service.dispatch("user_config")
        menus = self.env["shopfloor.menu"].search([])
        profiles = self.env["shopfloor.profile"].search([])
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
