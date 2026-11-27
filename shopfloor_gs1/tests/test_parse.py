# Copyright 2026 ACSONE SA/NV def parse(self, barcode):
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo.addons.shopfloor.tests.test_actions_search import TestSearchBaseCase

from .common import DATE, LOT1, MANUF_CODE, PROD_GTIN14


class TestParse(TestSearchBaseCase):
    def test_parse_gs1(self):
        parser = self.search.parser
        qty = 10
        barcode = f"(01){PROD_GTIN14}(17){DATE}(10){LOT1}(37){qty}"
        parsed_result = parser.parse(barcode)

        self.assertSetEqual(
            set(parsed_result.keys()),
            {"unknown", "product", "lot", "expiration_date", "qty"},
        )
        self.assertEqual(parsed_result["product"].raw, PROD_GTIN14)
        self.assertEqual(parsed_result["lot"].raw, LOT1)
        self.assertEqual(parsed_result["expiration_date"].raw, DATE)
        self.assertEqual(parsed_result["qty"].value, qty)

    def test_parse_precedence(self):
        parser = self.search.parser

        # Ensure (17) is favored for expiration date
        best_before_date = "180101"
        barcode = f"(01){PROD_GTIN14}(17){DATE}(15){best_before_date}"
        parsed_result = parser.parse(barcode)
        self.assertEqual(parsed_result["expiration_date"].raw, DATE)

        # Ensure (240) is favored for product barcode
        barcode = f"(01){PROD_GTIN14}(240){MANUF_CODE}"
        parsed_result = parser.parse(barcode)
        self.assertEqual(parsed_result["product"].raw, MANUF_CODE)
