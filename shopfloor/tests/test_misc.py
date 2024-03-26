# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import exceptions
from odoo.tests.common import TransactionCase

# pylint: disable=missing-return


class MiscTestCase(TransactionCase):
    tracking_disable = True

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(
            context=dict(cls.env.context, tracking_disable=cls.tracking_disable)
        )

    def test_package_name_unique(self):
        create = self.env["stock.quant.package"].create
        create({"name": "GOOD_NAME"})
        with self.assertRaises(exceptions.UserError) as exc:
            create({"name": "GOOD_NAME"})
        self.assertEqual(exc.exception.args[0], "Package name must be unique!")
