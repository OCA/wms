from .common import CommonCase


class TestOpenAPICommonCase(CommonCase):
    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)

        # we don't really care about which menu and profile we use
        # to read the OpenAPI specs
        cls.menu = cls.env.ref("shopfloor.shopfloor_menu_delivery")
        cls.process = cls.menu.process_id
        cls.profile = cls.env.ref("shopfloor.shopfloor_profile_shelf_1_demo")

    def setUp(self):
        super().setUp()

    def test_openapi(self):
        with self.work_on_services(menu=self.menu, profile=self.profile) as work:
            services = work.many_components()
            for service in services:
                if not service._is_rest_service_component:
                    continue
                # will raise if it fails to generate the openapi specs
                service.to_openapi()
