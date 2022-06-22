# Copyright 2021 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
# @author Simone Orsi <simahawk@gmail.com>

from .common import CommonCase


class TestSearchBaseCase(CommonCase):
    @classmethod
    def setUpClassVars(cls):
        super().setUpClassVars()
        with cls.work_on_actions(cls) as work:
            cls.search = work.component(usage="search")


class TestSearchCase(TestSearchBaseCase):
    def test_search_location(self):
        rec = self.customer_location
        handler = self.search.location_from_scan
        self.assertEqual(handler(rec.barcode), rec)
        self.assertEqual(handler(rec.name), rec)
        self.assertEqual(handler(False), rec.browse())
        self.assertEqual(handler("NONE"), rec.browse())

    def test_search_location_with_limit(self):
        rec = self.customer_location
        rec2 = self.customer_location.sudo().copy({"barcode": "CUSTOMERS2"})
        handler = self.search.location_from_scan
        res = handler("Customers", 2)
        self.assertEqual(res, rec + rec2)

    def test_search_package(self):
        rec = self.env["stock.quant.package"].sudo().create({"name": "1234"})
        handler = self.search.package_from_scan
        self.assertEqual(handler(rec.name), rec)
        self.assertEqual(handler(False), rec.browse())
        self.assertEqual(handler("NONE"), rec.browse())

    def test_search_picking(self):
        ptype = self.env.ref("shopfloor.picking_type_single_pallet_transfer_demo")
        rec = self._create_picking(picking_type=ptype)
        handler = self.search.picking_from_scan
        self.assertEqual(handler(rec.name), rec)
        self.assertEqual(handler(False), rec.browse())
        self.assertEqual(handler("NONE"), rec.browse())

    def test_search_product(self):
        rec = self.product_a
        handler = self.search.product_from_scan
        self.assertEqual(handler(rec.barcode), rec)
        self.assertEqual(handler(False), rec.browse())
        self.assertEqual(handler("NONE"), rec.browse())
        # It is not possible to search a product by packaging
        packaging = self.product_a_packaging
        self.assertFalse(handler(packaging.barcode))

    def test_search_lot_number_unique(self):
        rec = (
            self.env["stock.production.lot"]
            .sudo()
            .create(
                {"product_id": self.product_a.id, "company_id": self.env.company.id}
            )
        )
        handler = self.search.lot_from_scan
        self.assertEqual(handler(rec.name, products=self.product_a), rec)
        self.assertEqual(handler(False), rec.browse())
        self.assertEqual(handler("NONE"), rec.browse())

    def test_search_lot_number_shared_with_multiple_products(self):
        lot_model = self.env["stock.production.lot"].sudo()
        lots = (
            lot_model.create(
                {
                    "name": "TEST",
                    "product_id": self.product_a.id,
                    "company_id": self.env.company.id,
                }
            ),
            lot_model.create(
                {
                    "name": "TEST",
                    "product_id": self.product_b.id,
                    "company_id": self.env.company.id,
                }
            ),
        )
        handler = self.search.lot_from_scan
        self.assertEqual(handler(lots[0].name, products=self.product_a), lots[0])
        self.assertEqual(handler(lots[1].name, products=self.product_a), lots[0])
        self.assertEqual(handler(lots[0].name, products=self.product_b), lots[1])
        self.assertEqual(handler(lots[1].name, products=self.product_b), lots[1])

    def test_search_generic_packaging(self):
        rec = (
            self.env["product.packaging"]
            .sudo()
            .create({"name": "TEST PKG", "barcode": "1234"})
        )
        handler = self.search.generic_packaging_from_scan
        self.assertEqual(handler(rec.barcode), rec)
        self.assertEqual(handler(False), rec.browse())
        self.assertEqual(handler("NONE"), rec.browse())
