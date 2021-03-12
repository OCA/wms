# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from .common import CommonCase
from .common_misc import MenuTestMixin


class MenuCase(CommonCase, MenuTestMixin):
    @classmethod
    def setUpClassVars(cls):
        super().setUpClassVars()
        cls.profile = cls.env.ref("shopfloor_base.profile_demo_2")

    def test_menu_search(self):
        """Request /menu/search"""
        service = self._get_service()
        # Simulate the client searching menus
        response = service.dispatch("search")
        menus = self.env["shopfloor.menu"].search([])
        self._assert_menu_response(response, menus)

    def test_menu_search_restricted(self):
        """Request /menu/search with profile attributions"""
        # Simulate the client searching menus
        menus = self.env["shopfloor.menu"].sudo().search([])
        menus_without_profile = menus[0:2]
        # these menus should now be hidden for the current profile
        other_profile = self.env.ref("shopfloor_base.profile_demo_1")
        menus_without_profile.profile_id = other_profile

        service = self._get_service()
        response = service.dispatch("search")

        my_menus = menus - menus_without_profile
        self._assert_menu_response(response, my_menus)
