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
        cls.packaging = (
            cls.env["product.packaging"]
            .sudo()
            .create(
                {
                    "name": "Test Packaging",
                    # ↓ a valid GTIN-13 barcode
                    "barcode": "1642579575238",
                    "product_id": cls.product.id,
                }
            )
        )

    def test_find_gtin13_with_leading_zero(self):
        res = self.search.find(
            "0" + self.product.barcode,
        )
        self.assertEqual(res.record, self.product)

        res = self.search.find(
            "0" + self.packaging.barcode,
        )
        self.assertEqual(res.record, self.packaging)

    def test_find_gtin14_without_leading_zero(self):
        self.product.sudo().barcode = "0" + self.product.barcode
        self.packaging.sudo().barcode = "0" + self.packaging.barcode

        res = self.search.find(
            self.product.barcode[1:],
        )
        self.assertEqual(res.record, self.product)

        res = self.search.find(
            self.packaging.barcode[1:],
        )
        self.assertEqual(res.record, self.packaging)
