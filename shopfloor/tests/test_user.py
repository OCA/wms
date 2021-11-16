# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import mock

from .test_menu_base import CommonMenuCase


class UserCase(CommonMenuCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Hack to isolate data for testing.
        # Menu items can be added by any third party module
        # and we want to make sure we work only w/ the subset described here.
        ref = cls.env.ref
        xids = [
            "shopfloor.shopfloor_menu_single_pallet_transfer",
            "shopfloor.shopfloor_menu_zone_picking",
            "shopfloor.shopfloor_menu_cluster_picking",
            "shopfloor.shopfloor_menu_checkout",
            "shopfloor.shopfloor_menu_delivery",
            "shopfloor.shopfloor_menu_location_content_transfer",
            "shopfloor_base.shopfloor_menu_demo_1",
        ]
        menu_model = cls.env["shopfloor.menu"]

        def mocked_search(self, *args, **kwargs):
            return mocked_search.orig_search(*args, **kwargs).filtered(
                lambda x: x.id in mocked_search.limited_menu_item_ids
            )

        mocked_search.orig_search = menu_model.search
        mocked_search.limited_menu_item_ids = [ref(x).id for x in xids]

        cls.patcher = mock.patch.object(type(menu_model), "search", mocked_search)
        cls.patcher.start()

    @classmethod
    def tearDownClass(cls):
        cls.patcher.stop()
        super().tearDownClass()

    @classmethod
    def setUpClassVars(cls, *args, **kwargs):
        super().setUpClassVars(*args, **kwargs)
        ref = cls.env.ref
        cls.profile = ref("shopfloor_base.profile_demo_1")
        cls.profile2 = ref("shopfloor_base.profile_demo_2")

    def setUp(self):
        super().setUp()
        with self.work_on_services(profile=self.profile) as work:
            self.service = work.component(usage="user")

    def test_menu_no_profile(self):
        """Request /user/menu"""
        # Simulate the client asking the menu w/out profile -> no menu
        self.service.work.profile = self.env["shopfloor.menu"].browse()
        response = self.service.dispatch("menu")
        self.assert_response(
            response, data={"menus": []},
        )

    def test_menu_by_profile(self):
        """Request /user/menu w/ a specific profile but no picking types"""

        # Current profile 1 matches only this menu item
        expected_menu = self.env.ref("shopfloor_base.shopfloor_menu_demo_1")
        response = self.service.dispatch("menu")
        self.assert_response(
            response, data={"menus": [self._data_for_menu_item(expected_menu)]},
        )

        # now all the rest but the 1st one
        self.service.work.profile = self.profile2
        menus = self.env["shopfloor.menu"].sudo().search([]) - expected_menu
        menus.sudo().profile_id = self.profile2
        response = self.service.dispatch("menu")
        self.assert_response(
            response,
            data={"menus": [self._data_for_menu_item(menu) for menu in menus]},
        )

    def test_user_info(self):
        """Request /user/user_info"""
        response = self.service.dispatch("user_info")
        self.assert_response(
            response,
            data={"user_info": {"id": self.env.user.id, "name": self.env.user.name}},
        )
