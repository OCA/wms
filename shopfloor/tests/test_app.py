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
        self.assert_response(
            response,
            data={
                "menus": [
                    {
                        "id": self.ANY,
                        "name": "Put-Away Reach Truck",
                        "process": {"id": self.ANY, "code": "single_pack_putaway"},
                    },
                    {
                        "id": self.ANY,
                        "name": "Single Pallet Transfer",
                        "process": {"id": self.ANY, "code": "single_pack_transfer"},
                    },
                    {
                        "id": self.ANY,
                        "name": "Cluster Picking",
                        "process": {"id": self.ANY, "code": "cluster_picking"},
                    },
                ],
                "profiles": [
                    {
                        "id": self.ANY,
                        "name": "Highbay Truck",
                        "warehouse": {"id": self.ANY, "name": "YourCompany"},
                    },
                    {
                        "id": self.ANY,
                        "name": "Shelf 1",
                        "warehouse": {"id": self.ANY, "name": "YourCompany"},
                    },
                ],
            },
        )
