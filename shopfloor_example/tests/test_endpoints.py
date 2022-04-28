# Copyright 2022 Camptocamp SA (http://www.camptocamp.com)
# @author Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo.addons.shopfloor_base.tests.common_http import HttpCommonCase


class TestServiceEndpointsCase(HttpCommonCase):
    @classmethod
    def setUpShopfloorApp(cls):
        cls.shopfloor_app = cls.env.ref("shopfloor_example.app_demo_api_key")

    @classmethod
    def setUpClassBaseData(cls):
        cls.api_key = cls.env.ref("shopfloor_mobile_base_auth_api_key.api_key_demo")
        cls.record = cls.env.ref("base.res_partner_4")
        cls.record.ref = "1234"
        cls.menu = cls.env.ref("shopfloor_example.shopfloor_menu_partners_demo")
        cls.profile = cls.env.ref(
            "shopfloor_example.shopfloor_profile_partner_manager_demo"
        )

    def test_call_scan(self):
        route = self.shopfloor_app.api_url_for_service("partner_example", "scan")
        response = self._make_request(
            route + "/1234", menu=self.menu, profile=self.profile, api_key=self.api_key
        )
        self.assertEqual(response.status_code, 200)

    def test_call_partner_list(self):
        route = self.shopfloor_app.api_url_for_service(
            "partner_example", "partner_list"
        )
        response = self._make_request(
            route, menu=self.menu, profile=self.profile, api_key=self.api_key
        )
        self.assertEqual(response.status_code, 200)

    def test_call_detail(self):
        route = self.shopfloor_app.api_url_for_service("partner_example", "detail")
        response = self._make_request(
            route + "/1234", menu=self.menu, profile=self.profile, api_key=self.api_key
        )
        self.assertEqual(response.status_code, 200)
