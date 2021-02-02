# Copyright 2021 ACSONE SA/NV (http://www.camptocamp.com)
# @author Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import Form

from .common import CommonCase


class TestShopfloorRecords(CommonCase):
    @classmethod
    def setUpClassUsers(cls):
        super().setUpClassUsers()
        cls.env = cls.env(user=cls.shopfloor_manager)

    def test_scenario(self):
        rec = self.env["shopfloor.scenario"].create(
            {
                "name": "New Scenario",
                "options_edit": """
opt1: true
opt2: false
opt3:
    nested: true
            """,
            }
        )
        self.assertEqual(rec.key, "new_scenario")
        # fmt: off
        self.assertEqual(rec.options, {
            "opt1": True,
            "opt2": False,
            "opt3": {
                "nested": True,
            },
        })
        # fmt: on
        with Form(self.env["shopfloor.scenario"]) as form:
            form.name = "Test Onchange"
            self.assertEqual(form.key, "test_onchange")

    # TODO: test other records (menu, profile)
