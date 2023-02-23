# Copyright 2023 Camptocamp SA (http://www.camptocamp.com)
# @author Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.shopfloor.tests.test_actions_data_base import ActionsDataDetailCaseBase
from odoo.addons.shopfloor_base.tests.common_misc import ScanAnythingTestMixin

from .common import (
    GS1_GTIN_BARCODE_1,
    GS1_MANUF_BARCODE,
    LOT1,
    MANUF_CODE,
    PROD_BARCODE,
)


class ScanAnythingCase(ActionsDataDetailCaseBase, ScanAnythingTestMixin):
    def test_scan_product(self):
        record = self.product_b
        record.barcode = PROD_BARCODE
        record.default_code = MANUF_CODE
        rec_type = "product"
        data = self.data_detail.product_detail(record)
        # All kinds of search supported
        for identifier in (
            GS1_GTIN_BARCODE_1,
            GS1_MANUF_BARCODE,
            record.barcode,
            record.default_code,
        ):
            self._test_response_ok(rec_type, data, identifier)

    def test_find_location(self):
        record = self.stock_location
        rec_type = "location"
        gs1_barcode = GS1_GTIN_BARCODE_1 + "(254)" + record.name
        data = self.data_detail.location_detail(record)
        for identifier in (gs1_barcode, record.name):
            self._test_response_ok(rec_type, data, identifier)

    def test_scan_package(self):
        record = self.package
        rec_type = "package"
        identifier = record.name
        data = self.data_detail.package_detail(record)
        self._test_response_ok(rec_type, data, identifier)

    def test_scan_lot(self):
        record = (
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
        rec_type = "lot"
        identifier = record.name
        data = self.data_detail.lot_detail(record)
        for identifier in (GS1_GTIN_BARCODE_1, record.name):
            self._test_response_ok(rec_type, data, identifier)

    def test_scan_transfer(self):
        record = self.picking
        rec_type = "transfer"
        identifier = record.name
        data = self.data_detail.picking_detail(record)
        self._test_response_ok(rec_type, data, identifier)
