# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.shopfloor_base.tests.common import CommonCase


# pylint: disable=missing-return
class TestShopfloorScenario(CommonCase):
    @classmethod
    def setUpClassUsers(cls):
        super().setUpClassUsers()
        cls.env = cls.env(user=cls.shopfloor_manager)

    def test_scenario(self):
        scenario = self.env.ref("shopfloor.scenario_location_content_transfer")
        self.assertTrue(scenario.options["full_location_reservation"])
