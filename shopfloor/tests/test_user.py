# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from .test_menu_base import CommonMenuCase

# pylint: disable=missing-return


class UserCase(CommonMenuCase):
    @classmethod
    def setUpClassVars(cls, *args, **kwargs):
        super().setUpClassVars(*args, **kwargs)
        ref = cls.env.ref
        cls.wms_profile = ref("shopfloor.profile_demo_1")
        cls.wms_profile2 = ref("shopfloor.profile_demo_2")

    def test_menu_by_profile(self):
        """Request /user/menu w/ a specific profile but no picking types"""

        service = self.get_service("user", profile=self.wms_profile)
        menus = (
            self.env["shopfloor.menu"]
            .sudo()
            .search([("profile_id", "=", self.wms_profile.id)])
        )
        response = service.dispatch("menu")
        self.assert_response(
            response,
            data={"menus": [self._data_for_menu_item(menu) for menu in menus]},
        )

        service = self.get_service("user", profile=self.wms_profile2)
        menus = (
            self.env["shopfloor.menu"]
            .sudo()
            .search([("profile_id", "=", self.wms_profile2.id)])
        )
        response = service.dispatch("menu")
        self.assert_response(
            response,
            data={"menus": [self._data_for_menu_item(menu) for menu in menus]},
        )
