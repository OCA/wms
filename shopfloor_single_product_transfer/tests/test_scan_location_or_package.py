# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from .common import CommonCase


class TestScanLocation(CommonCase):
    def test_scan_barcode_not_found(self):
        response = self.service.dispatch(
            "scan_location_or_package", params={"barcode": "NOPE"}
        )
        expected_message = {
            "message_type": "error",
            "body": "Barcode not found",
        }
        self.assert_response(
            response,
            next_state="select_location_or_package",
            data={},
            message=expected_message,
        )

    def test_scan_wrong_location(self):
        location = self.location_customer
        response = self.service.dispatch(
            "scan_location_or_package", params={"barcode": location.name}
        )
        expected_message = {
            "message_type": "error",
            "body": f"The content of {location.name} cannot be transferred with this scenario.",
        }
        self.assert_response(
            response,
            next_state="select_location_or_package",
            data={},
            message=expected_message,
        )

    def test_scan_empty_location(self):
        location = self.child_location
        response = self.service.dispatch(
            "scan_location_or_package", params={"barcode": location.name}
        )
        expected_message = {
            "message_type": "error",
            "body": f"Location {location.name} empty",
        }
        self.assert_response(
            response,
            next_state="select_location_or_package",
            data={},
            message=expected_message,
        )

    def test_scan_location_ok(self):
        self._enable_create_move_line()
        location = self.location_src

        response = self.service.dispatch(
            "scan_location_or_package", params={"barcode": location.name}
        )
        self.assert_response(
            response,
            next_state="select_product",
            data={"location": self._data_for_location(location)},
        )

    def test_scan_location_stock_packages(self):
        location = self.location_src
        package = self.env["stock.quant.package"].sudo().create({})
        for quant in location.quant_ids:
            quant.sudo().package_id = package

        response = self.service.dispatch(
            "scan_location_or_package", params={"barcode": location.name}
        )
        expected_message = {
            "message_type": "warning",
            "body": "This location only contains packages, please scan one of them.",
        }
        self.assert_response(
            response,
            next_state="select_location_or_package",
            data={},
            message=expected_message,
        )

    def test_scan_location_only_lines_with_package(self):
        location = self.location_src
        package = self.env["stock.quant.package"].sudo().create({})
        for line in location.source_move_line_ids:
            # There are no lines without a package in this location.
            line.package_id = package

        # Scan a location, user is asked to scan a package.
        response = self.service.dispatch(
            "scan_location_or_package", params={"barcode": location.name}
        )
        expected_message = {
            "message_type": "warning",
            "body": "This location only contains packages, please scan one of them.",
        }
        self.assert_response(
            response,
            next_state="select_location_or_package",
            data={},
            message=expected_message,
        )

        # Scan a package.
        response = self.service.dispatch(
            "scan_location_or_package", params={"barcode": package.name}
        )
        self.assert_response(
            response,
            next_state="select_product",
            data={
                "location": self._data_for_location(package.location_id),
                "package": self._data_for_package(
                    package, with_operation_progress_src=True
                ),
            },
        )
