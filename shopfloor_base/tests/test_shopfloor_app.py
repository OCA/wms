# Copyright 2021 Camptocamp SA (http://www.camptocamp.com)
# @author Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
from odoo.addons.shopfloor_base.utils import APP_VERSION

from .common import CommonCase


# @tagged("-at_install")
class TestShopfloorApp(CommonCase):
    @classmethod
    def setUpClassUsers(cls):
        super().setUpClassUsers()
        cls.env = cls.env(user=cls.shopfloor_manager)

    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()
        cls.records = cls.env["shopfloor.app"].create(
            {
                "name": "A wonderful test app",
                "tech_name": "test_app",
                "short_name": "Test app",
            }
        ) + cls.env["shopfloor.app"].create(
            {
                "name": "A wonderful test app 2",
                "tech_name": "test_app_2",
                "short_name": "Test app 2",
            }
        )

    def test_app_create(self):
        # fmt: off
        expected = [
            {
                "api_route": "/shopfloor/api/test_app",
                "url": "/shopfloor/app/test_app",
            },
            {
                "api_route": "/shopfloor/api/test_app_2",
                "url": "/shopfloor/app/test_app_2",
            },
        ]
        # fmt: on
        self.assertRecordValues(self.records, expected)

    def _test_registered_routes(self, rec):
        # On class setup the registry is not ready thus endpoints are not registered yet
        rec._register_endpoints()
        routes = rec._registered_routes()
        _check = {}
        endpoint_func_repr = (
            "bound method _process_endpoint "
            "of <odoo.addons.base_rest.controllers.main.RestController"
        )
        for __, rule in routes:
            self.assertEqual(rule.route_group, rec._route_group())
            self.assertTrue(rule.endpoint_hash)
            self.assertIn(endpoint_func_repr, repr(rule.endpoint.method.func))
            _check[rule.route] = set(rule.routing["methods"])
        expected = {
            # TODO: review methods
            f"/shopfloor/api/{rec.tech_name}/app/user_config": {"POST"},
            f"/shopfloor/api/{rec.tech_name}/user/menu": {"POST"},
            f"/shopfloor/api/{rec.tech_name}/user/user_info": {"POST"},
            f"/shopfloor/api/{rec.tech_name}/menu/search": {
                "GET",
            },
            f"/shopfloor/api/{rec.tech_name}/profile/search": {
                "GET",
            },
            f"/shopfloor/api/{rec.tech_name}/scan_anything/scan": {"POST"},
        }
        for route, method in expected.items():
            self.assertEqual(
                _check[route], method, f"{route}: {method} != {_check[route]}"
            )

        expected = sorted([f"{k} ({', '.join(v)})" for k, v in expected.items()])
        rec.invalidate_cache(["registered_routes"])
        self.assertEqual(
            sorted(rec.registered_routes.splitlines()),
            expected,
            f"{rec.tech_name} failed",
        )

    def test_registered_routes(self):
        rec1, rec2 = self.records
        self._test_registered_routes(rec1)
        self._test_registered_routes(rec2)
        # TODO: test after routing_map cleaned

    def test_api_url_for_service(self):
        app = self.shopfloor_app
        self.assertEqual(
            app.api_url_for_service("profile"),
            f"/shopfloor/api/{app.tech_name}/profile",
        )
        self.assertEqual(
            app.api_url_for_service("profile", "search"),
            f"/shopfloor/api/{app.tech_name}/profile/search",
        )
        self.assertEqual(
            app.api_url_for_service("app", "user_config"),
            f"/shopfloor/api/{app.tech_name}/app/user_config",
        )

    def test_make_app_info(self):
        info = self.shopfloor_app._make_app_info()
        expected = {
            "auth_type": "user_endpoint",
            "base_url": "/shopfloor/api/test/",
            "demo_mode": False,
            "manifest_url": "/shopfloor/app/test/manifest.json",
            "name": "Test",
            "profile_required": False,
            "running_env": "prod",
            "short_name": "test",
            "version": APP_VERSION,
        }
        self.assertEqual(info, expected)
        info = self.shopfloor_app._make_app_info(demo=True)
        self.assertEqual(info["demo_mode"], True)
