from .common import CommonCase


class MenuCase(CommonCase):
    def setUp(self):
        super().setUp()
        with self.work_on_services() as work:
            self.service = work.component(usage="menu")

    def test_to_openapi(self):
        # will raise if it fails to generate the openapi specs
        self.service.to_openapi()

    def test_menu_search(self):
        """Request /menu/search"""
        # Simulate the client searching menus
        response = self.service.dispatch("search")
        self.assert_response(
            response,
            data={
                "size": 3,
                "records": [
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
            },
        )
