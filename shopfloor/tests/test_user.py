# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from .common import CommonCase


class UserCase(CommonCase):
    @classmethod
    def setUpClassVars(cls, *args, **kwargs):
        super().setUpClassVars(*args, **kwargs)
        cls.profile = cls.env.ref("shopfloor.shopfloor_profile_hb_truck_demo")
        cls.profile2 = cls.env.ref("shopfloor.shopfloor_profile_shelf_1_demo")

    def setUp(self):
        super().setUp()
        with self.work_on_services(profile=self.profile) as work:
            self.service = work.component(usage="user")

    def test_menu_no_profile(self):
        """Request /user/menu"""
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
        """Request /user/menu w/ a specific profile"""
        # Simulate the client asking the menu
        menus = self.env["shopfloor.menu"].sudo().search([])
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
