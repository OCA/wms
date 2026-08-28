# Copyright 2026 ACSONE SA/NV def parse(self, barcode):
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo.addons.shopfloor.tests.test_actions_search import TestSearchBaseCase

from .common import DATE, LOT1, PROD_GTIN14


class TestParse(TestSearchBaseCase):
    def test_parse_gs1(self):
        parser = self.search.parser
        barcode = f"(01){PROD_GTIN14}(17){DATE}(10){LOT1}"
        parsed_result = parser.parse(barcode)

        self.assertSetEqual(
            set(parsed_result.keys()),
            {
                "unknown",
                "product",
                "lot",
                "expiration_date",
            },
        )
        self.assertEqual(parsed_result["product"].raw, PROD_GTIN14)
        self.assertEqual(parsed_result["lot"].raw, LOT1)
        self.assertEqual(parsed_result["expiration_date"].raw, DATE)
