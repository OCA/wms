# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from .test_checkout_base import CheckoutCommonCase


class CheckoutScanCase(CheckoutCommonCase):
    def _test_scan_ok(self, barcode_func):
        picking = self._create_picking()
        self._fill_stock_for_moves(picking.move_lines, in_package=True)
        picking.action_assign()
        barcode = barcode_func(picking)
        response = self.service.dispatch("scan_document", params={"barcode": barcode})
        self.assert_response(
            response,
            next_state="select_line",
            data={"picking": self._stock_picking_data(picking)},
        )

    def test_scan_document_stock_picking_ok(self):
        self._test_scan_ok(lambda picking: picking.name)

    def test_scan_document_location_ok(self):
        self._test_scan_ok(lambda picking: picking.move_line_ids.location_id.barcode)

    def test_scan_document_package_ok(self):
        self._test_scan_ok(lambda picking: picking.move_line_ids.package_id.name)

    def test_scan_document_error_not_found(self):
        response = self.service.dispatch("scan_document", params={"barcode": "NOPE"})
        self.assert_response(
            response,
            next_state="select_document",
            message={"message_type": "error", "body": "Barcode not found"},
        )

    def _test_scan_document_error_not_available(self, barcode_func):
        picking = self._create_picking()
        # in this test, we want the picking not to be available, but
        # if we leave the shipping policy to direct, a single move assigned
        # would make the picking available
        picking.move_type = "one"
        # the picking will have one line available, so the endpoint can find
        # something from a location or package but should reject the picking as
        # it is not entirely available
        self._fill_stock_for_moves(picking.move_lines[0], in_package=True)
        picking.action_assign()
        barcode = barcode_func(picking)
        response = self.service.dispatch("scan_document", params={"barcode": barcode})
        self.assert_response(
            response,
            next_state="select_document",
            message={
                "message_type": "error",
                "body": "Transfer {} is not available.".format(picking.name),
            },
        )

    def test_scan_document_error_not_available_picking(self):
        self._test_scan_document_error_not_available(lambda picking: picking.name)

    def test_scan_document_error_not_available_location(self):
        self._test_scan_document_error_not_available(
            lambda picking: picking.move_line_ids.location_id.barcode
        )

    def test_scan_document_error_not_available_package(self):
        self._test_scan_document_error_not_available(
            lambda picking: picking.move_line_ids.package_id.name
        )

    def test_scan_document_error_location_not_child_of_type(self):
        picking = self._create_picking()
        picking.location_id = self.dispatch_location
        self._fill_stock_for_moves(picking.move_lines, in_package=True)
        picking.action_assign()
        response = self.service.dispatch(
            "scan_document", params={"barcode": picking.location_id.barcode}
        )
        self.assert_response(
            response,
            next_state="select_document",
            message={"message_type": "error", "body": "Location not allowed here."},
        )

    def _test_scan_document_error_different_picking_type(self, barcode_func):
        picking = self._create_picking(picking_type=self.wh.pick_type_id)
        self._fill_stock_for_moves(picking.move_lines, in_package=True)
        picking.action_assign()
        barcode = barcode_func(picking)
        response = self.service.dispatch("scan_document", params={"barcode": barcode})
        self.assert_response(
            response,
            next_state="select_document",
            message={
                "message_type": "error",
                "body": "You cannot move this using this menu.",
            },
        )

    def test_scan_document_error_different_picking_type_picking(self):
        self._test_scan_document_error_different_picking_type(
            lambda picking: picking.name
        )

    def test_scan_document_error_different_picking_type_package(self):
        self._test_scan_document_error_different_picking_type(
            lambda picking: picking.move_line_ids.package_id.name
        )

    def test_scan_document_error_location_several_pickings(self):
        picking = self._create_picking()
        # create a second picking at the same place so we don't
        # know which picking to use
        picking2 = self._create_picking()
        pickings = picking | picking2
        self._fill_stock_for_moves(pickings.move_lines, in_package=True)
        pickings.action_assign()
        response = self.service.dispatch(
            "scan_document",
            params={"barcode": picking.move_line_ids.location_id.barcode},
        )
        self.assert_response(
            response,
            next_state="select_document",
            message={
                "message_type": "error",
                "body": "Several transfers found, please scan a package"
                " or select a transfer manually.",
            },
        )
