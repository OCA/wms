# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from .test_manual_product_transfer_base import ManualProductTransferCommonCase


class ManualProductTransferStart(ManualProductTransferCommonCase):
    """Tests for start state

    Endpoints:

    * /scan_source_location
    """

    def test_scan_source_location_not_found(self):
        response = self.service.dispatch(
            "scan_source_location", params={"barcode": "UNKNOWN"}
        )
        self.assert_response_start(
            response, message=self.service.msg_store.no_location_found()
        )

    def test_scan_source_location_not_allowed(self):
        response = self.service.dispatch(
            "scan_source_location",
            params={"barcode": self.not_allowed_location.barcode},
        )
        self.assert_response_start(
            response, message=self.service.msg_store.location_not_allowed()
        )

    def test_scan_source_location_empty(self):
        response = self.service.dispatch(
            "scan_source_location", params={"barcode": self.empty_location.barcode}
        )
        self.assert_response_start(
            response, message=self.service.msg_store.location_empty(self.empty_location)
        )

    def test_scan_source_location(self):
        response = self.service.dispatch(
            "scan_source_location", params={"barcode": self.src_location.barcode}
        )
        self.assert_response_scan_product(response, self.src_location)
