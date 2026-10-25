# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.shopfloor.tests.test_actions_data_base import ActionsDataCaseBase


class TestShopfloorReceptionStockAvailable(ActionsDataCaseBase):
    def test_data_product_immediately_usable_qty(self):

        data = self.data.product(self.product_a)
        expected = {
            "immediately_usable_qty": 0,
        }
        self.assertDictContainsSubset(expected, data)
