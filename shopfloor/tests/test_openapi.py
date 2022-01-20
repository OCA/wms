# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.shopfloor_base.tests.common_misc import OpenAPITestMixin

from .common import CommonCase


class TestOpenAPICommonCase(CommonCase, OpenAPITestMixin):
    @classmethod
    def setUpClassVars(cls):
        super().setUpClassVars()
        # we don't really care about which menu and profile we use
        # to read the OpenAPI specs
        cls.menu = cls.env.ref("shopfloor.shopfloor_menu_demo_delivery")
        cls.profile = cls.env.ref("shopfloor_base.profile_demo_1")

    def test_openapi(self):
        self._test_openapi(menu=self.menu, profile=self.profile)
