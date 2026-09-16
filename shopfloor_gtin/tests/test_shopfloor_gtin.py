# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo.addons.shopfloor.tests.test_actions_search import TestSearchBaseCase


class TestShopfloorGtin(TestSearchBaseCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = (
            cls.env["product.product"]
            .sudo()
            .create(
                {
                    "name": "Test Product",
                    # ↓ a valid GTIN-13 barcode
                    "barcode": "1260619202601",
                }
            )
        )

    def test_find_gtin13_with_leading_zero(self):
        res = self.search.find(
            "0" + self.product.barcode,
        )
        self.assertEqual(res.record, self.product)
