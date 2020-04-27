from .common import CommonCase


class MenuCase(CommonCase):
    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)
        cls.profile = cls.env.ref("shopfloor.shopfloor_profile_shelf_1_demo")

    def setUp(self):
        super().setUp()
        with self.work_on_services(profile=self.profile) as work:
            self.service = work.component(usage="menu")

    def test_menu_search(self):
        """Request /menu/search"""
        # Simulate the client searching menus
        response = self.service.dispatch("search")
        menus = self.env["shopfloor.menu"].search([])
        self.assert_response(
            response,
            data={
                "size": len(menus),
                "records": [
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
                ],
            },
        )

    def test_menu_search_restricted(self):
        """Request /menu/search with profile attributions"""
        # Simulate the client searching menus
        menus = self.env["shopfloor.menu"].search([])
        menus_without_profile = menus[0:2]
        # these menus should now be hidden for the current profile
        other_profile = self.env.ref("shopfloor.shopfloor_profile_hb_truck_demo")
        menus_without_profile.profile_ids = other_profile

        response = self.service.dispatch("search")

        my_menus = menus - menus_without_profile
        self.assert_response(
            response,
            data={
                "size": len(my_menus),
                "records": [
                    {
                        "id": menu.id,
                        "name": menu.name,
                        "scenario": menu.scenario,
                        "picking_types": [
                            {"id": picking_type.id, "name": picking_type.name}
                            for picking_type in menu.picking_type_ids
                        ],
                    }
                    for menu in my_menus
                ],
            },
        )
