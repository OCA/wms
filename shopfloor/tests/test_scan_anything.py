# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# Copyright 2021 ACSONE SA/NV (http://www.acsone.eu)
# @author Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.shopfloor_base.tests.common_misc import ScanAnythingTestMixin

from .test_actions_data_base import ActionsDataDetailCaseBase


class ScanAnythingCase(ActionsDataDetailCaseBase, ScanAnythingTestMixin):
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
