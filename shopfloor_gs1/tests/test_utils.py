# Copyright 2022 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime

from odoo.tests.common import BaseCase

from ..utils import GS1Barcode


class TestUtils(BaseCase):
    def test_parse1(self):
        code = "(01)09506000117843(11)141231(10)1234AB"
        res = GS1Barcode.parse(code)
        self.assertEqual(len(res), 3, res)
        item = [x for x in res if x.ai == "01"][0]
        self.assertEqual(item.code, code)
        self.assertEqual(item.value, "9506000117843")
        self.assertEqual(item.raw_value, "09506000117843")
        item = [x for x in res if x.ai == "11"][0]
        self.assertEqual(item.code, code)
        self.assertEqual(item.value, datetime.date(2014, 12, 31))
        self.assertEqual(item.raw_value, "141231")
        item = [x for x in res if x.ai == "10"][0]
        self.assertEqual(item.code, code)
        self.assertEqual(item.value, "1234AB")
        self.assertEqual(item.raw_value, "1234AB")

    def test_parse2(self):
        code = "(01)09506000117843(11)141231(10)1234AB"
        res = GS1Barcode.parse(code, ai_whitelist=("01",))
        self.assertEqual(len(res), 1, res)
        item = [x for x in res if x.ai == "01"][0]
        self.assertEqual(item.code, code)
        self.assertEqual(item.value, "9506000117843")
        self.assertEqual(item.raw_value, "09506000117843")

    def test_parse3(self):
        code = "(240)K000075(11)230201(10)0000392"
        res = GS1Barcode.parse(code, ai_whitelist=("240",))
        self.assertEqual(len(res), 1, res)
        item = [x for x in res if x.ai == "240"][0]
        self.assertEqual(item.code, code)
        self.assertEqual(item.value, "K000075")
        self.assertEqual(item.raw_value, "K000075")

    def test_parse_order(self):
        """Ensure ai whitelist order is respected"""
        code = "(01)09506000117843(11)141231(10)1234AB"
        res = GS1Barcode.parse(code, ai_whitelist=("10", "01", "11"))
        self.assertEqual(len(res), 3, res)
        self.assertEqual(res[0].ai, "10")
        self.assertEqual(res[1].ai, "01")
        self.assertEqual(res[2].ai, "11")
        res = GS1Barcode.parse(code, ai_whitelist=("01", "11", "10"))
        self.assertEqual(len(res), 3, res)
        self.assertEqual(res[0].ai, "01")
        self.assertEqual(res[1].ai, "11")
        self.assertEqual(res[2].ai, "10")

    def test_barcode(self):
        code = "(01)09506000117843(11)141231(10)1234AB"
        res = GS1Barcode.parse(code)
        res_2 = GS1Barcode.parse(code)

        self.assertTrue(res[0] == res_2[0])

        self.assertFalse(res[0] == res_2[1])
        self.assertFalse(res[0] == list())

        self.assertTrue(res[0])
        self.assertFalse(GS1Barcode())

        self.assertEqual(str(res[0]), "<GS1Barcode: ai=01>")

    def test_parse_single_sscc(self):
        code = "(00)354123450000000014"
        res = GS1Barcode.parse(code)
        self.assertEqual(len(res), 1, res)
        item = [x for x in res if x.ai == "00"][0]
        self.assertEqual(item.code, code)
        self.assertEqual(item.value, "354123450000000014")
        self.assertEqual(item.raw_value, "354123450000000014")

    def test_do_not_parse_invalid_gs1(self):
        # Do not parse if no primary AI
        code = "(10)LOT"
        res = GS1Barcode.parse(code)
        self.assertFalse(res)

        # Do not parse if invalid GS1 format
        # 00 AI should be of the form (\d{18}), see https://ref.gs1.org/ai/00
        code = "(00)PACK1"
        res = GS1Barcode.parse(code)
        self.assertFalse(res)
