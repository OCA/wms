# Copyright 2022 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.addons.shopfloor.tests.test_actions_search import TestSearchBaseCase

from .common import (
    GS1_GTIN_BARCODE_1,
    GS1_MANUF_BARCODE,
    LOT1,
    MANUF_CODE,
    PROD_BARCODE,
)


class TestFind(TestSearchBaseCase):
    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()
        cls.product_a.barcode = PROD_BARCODE

    def test_find_picking(self):
        ptype = self.env.ref("shopfloor.picking_type_single_pallet_transfer_demo")
        rec = self._create_picking(picking_type=ptype)
        res = self.search.find(rec.name, types=("picking",))
        self.assertEqual(res.record, rec)

    def test_find_location(self):
        rec = self.customer_location
        barcode = GS1_GTIN_BARCODE_1 + "(254)" + rec.name
        res = self.search.find(barcode, types=("location",))
        self.assertEqual(res.record, rec)
        res = self.search.find(rec.name, types=("location",))
        self.assertEqual(res.record, rec)

    def test_find_package(self):
        rec = self.env["stock.quant.package"].sudo().create({"name": "ABC1234"})
        res = self.search.find(rec.name, types=("package",))
        self.assertEqual(res.record, rec)

    def test_find_product(self):
        rec = self.product_a
        res = self.search.find(GS1_GTIN_BARCODE_1, types=("product",))
        self.assertEqual(res.record, rec)
        rec.barcode = MANUF_CODE
        res = self.search.find(GS1_MANUF_BARCODE, types=("product",))
        self.assertEqual(res.record, rec)

    def test_find_lot(self):
        rec = (
            self.env["stock.production.lot"]
            .sudo()
            .create(
                {
                    "product_id": self.product_a.id,
                    "company_id": self.env.company.id,
                    "name": LOT1,
                }
            )
        )
        res = self.search.find(
            GS1_GTIN_BARCODE_1,
            types=("lot",),
            handler_kw=dict(lot=dict(products=self.product_a)),
        )
        self.assertEqual(res.record, rec)

    def test_find_generic_packaging(self):
        rec = (
            self.env["product.packaging"]
            .sudo()
            .create({"name": "TEST PKG", "barcode": "1234"})
        )
        res = self.search.find(rec.barcode, types=("delivery_packaging",))
        self.assertEqual(res.record, rec)
