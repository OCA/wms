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
        menus_without_profile.profile_ids = other_profile

        response = self.service.dispatch("search")

        my_menus = menus - menus_without_profile
        self._assert_menu_response(response, my_menus)

    def test_menu_search_warehouse_filter(self):
        """Request /menu/search with different warehouse on profile"""
        menus = self.env["shopfloor.menu"].sudo().search([])
        # should not be visible as the profile has another wh
        menu_different_wh = menus[0]
        other_wh = (
            self.env["stock.warehouse"].sudo().create({"name": "Test", "code": "test"})
        )
        menu_different_wh.picking_type_ids.warehouse_id = other_wh

        # should be visible to any profile
        menu_no_wh = menus[1]
        menu_no_wh.picking_type_ids.warehouse_id = False

        response = self.service.dispatch("search")

        self._assert_menu_response(response, menus - menu_different_wh)
