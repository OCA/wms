# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from .test_menu_base import CommonMenuCase


class MenuCase(CommonMenuCase):
    def test_menu_search(self):
        """Request /menu/search"""
        # Simulate the client searching menus
        response = self.service.dispatch("search")
        menus = self.env["shopfloor.menu"].search([])
        self._assert_menu_response(response, menus)

    def test_menu_search_restricted(self):
        """Request /menu/search with profile attributions"""
        # Simulate the client searching menus
        menus = self.env["shopfloor.menu"].sudo().search([])
        menus_without_profile = menus[0:2]
        # these menus should now be hidden for the current profile
        other_profile = self.env.ref("shopfloor.shopfloor_profile_hb_truck_demo")
        menus_without_profile.profile_id = other_profile

        response = self.service.dispatch("search")

        my_menus = menus - menus_without_profile
        self._assert_menu_response(response, my_menus)
