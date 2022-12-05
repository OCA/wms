# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from .common import CommonCase


class TestScanLocation(CommonCase):
    def test_scan_location_not_found(self):
        response = self.service.dispatch("scan_location", params={"barcode": "NOPE"})
        expected_message = {
            "message_type": "error",
            "body": "No location found for this barcode.",
        }
        self.assert_response(
            response, next_state="select_location", data={}, message=expected_message
        )

    def test_scan_wrong_location(self):
        location = self.location_customer
        response = self.service.dispatch(
            "scan_location", params={"barcode": location.name}
        )
        expected_message = {
            "message_type": "error",
            "body": f"The content of {location.name} cannot be transferred with this scenario.",
        }
        self.assert_response(
            response, next_state="select_location", data={}, message=expected_message
        )

    def test_scan_empty_location(self):
        location = self.child_location
        response = self.service.dispatch(
            "scan_location", params={"barcode": location.name}
        )
        expected_message = {
            "message_type": "error",
            "body": f"Location {location.name} empty",
        }
        self.assert_response(
            response, next_state="select_location", data={}, message=expected_message
        )

    def test_scan_location_ok(self):
        location = self.location_src
        response = self.service.dispatch(
            "scan_location", params={"barcode": location.name}
        )
        self.assert_response(
            response,
            next_state="select_product",
            data={"location": self._data_for_location(location)},
        )
