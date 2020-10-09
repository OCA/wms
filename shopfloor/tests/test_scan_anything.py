# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from .test_actions_data_detail import ActionsDataDetailCaseBase


class ScanAnythingCase(ActionsDataDetailCaseBase):
    def setUp(self):
        super().setUp()
        with self.work_on_services() as work:
            self.service = work.component(usage="scan_anything")

    def _test_response_ok(self, rec_type, data, identifier):
        params = {"identifier": identifier}
        response = self.service.dispatch("scan", params=params)
        self.assert_response(
            response, data={"type": rec_type, "identifier": identifier, "record": data},
        )

    def _test_response_ko(self, identifier, tried=None):
        tried = tried or [x[0] for x in self.service._scan_handlers()]
        params = {"identifier": identifier}
        response = self.service.dispatch("scan", params=params)
        message = response["message"]
        self.assertEqual(message["message_type"], "error")
        self.assertIn("Record not found", message["body"])
        for rec_type in tried:
            self.assertIn(rec_type, message["body"])

    def test_scan_product(self):
        record = self.product_b
        record.barcode = "PROD-B"
        rec_type = "product"
        identifier = record.barcode
        data = self.data_detail.product_detail(record)
        self._test_response_ok(rec_type, data, identifier)

    def test_scan_location(self):
        record = self.stock_location
        rec_type = "location"
        identifier = record.barcode
        data = self.data_detail.location_detail(record)
        self._test_response_ok(rec_type, data, identifier)

    def test_scan_package(self):
        record = self.package
        rec_type = "package"
        identifier = record.name
        data = self.data_detail.package_detail(record)
        self._test_response_ok(rec_type, data, identifier)

    def test_scan_lot(self):
        record = self.lot
        rec_type = "lot"
        identifier = record.name
        data = self.data_detail.lot_detail(record)
        self._test_response_ok(rec_type, data, identifier)

    def test_scan_transfer(self):
        record = self.picking
        rec_type = "transfer"
        identifier = record.name
        data = self.data_detail.picking_detail(record)
        self._test_response_ok(rec_type, data, identifier)

    def test_scan_error(self):
        self._test_response_ko("404-NOTFOUND")
