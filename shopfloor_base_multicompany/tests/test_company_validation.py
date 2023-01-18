# Copyright 2023 Camptocamp SA (http://www.camptocamp.com)
# @author Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import exceptions

from odoo.addons.shopfloor_base.tests.common import CommonCase


class TestCompanyCase(CommonCase):
    @classmethod
    def setUpClassVars(cls):
        super().setUpClassVars()
        cls.profile = cls.env.ref("shopfloor_base.profile_demo_2")

    def test_default(self):
        self.assertFalse(self.shopfloor_app.must_validate_company)
        service = self.get_service("menu", profile=self.profile)
        self.assertTrue(service.dispatch("search"))

    def test_company_restricted(self):
        # Note: use another user for creation
        # otherwise the company is automatically added to the current user
        new_comp = (
            self.env["res.company"]
            .with_user(self.shopfloor_manager)
            .sudo()
            .create({"name": "C2C"})
        )
        self.shopfloor_app.sudo().company_ids += new_comp
        self.assertTrue(self.shopfloor_app.must_validate_company)

        service = self.get_service("menu", profile=self.profile)
        msg = service._validate_company_error_msg()
        with self.assertRaisesRegex(exceptions.UserError, msg):
            service.dispatch("search")

        self.env.user.sudo().company_ids += new_comp
        self.env.user.sudo().company_id = new_comp
        self.assertTrue(service.dispatch("search"))
