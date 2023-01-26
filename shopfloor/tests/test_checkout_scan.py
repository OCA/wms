# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from .test_checkout_base import CheckoutCommonCase


class CheckoutScanCase(CheckoutCommonCase):
    def _test_scan_ok(self, barcode_func, in_package=True):
        picking = self._create_picking()
        self._fill_stock_for_moves(picking.move_lines, in_package=in_package)
        picking.action_assign()
        barcode = barcode_func(picking)
        response = self.service.dispatch("scan_document", params={"barcode": barcode})
        self.assert_response(
            response,
            next_state="select_line",
            data=self._data_for_select_line(picking),
        )

    def test_scan_document_stock_picking_ok(self):
        self._test_scan_ok(lambda picking: picking.name)

    def test_scan_document_location_ok(self):
        self._test_scan_ok(lambda picking: picking.move_line_ids.location_id.barcode)

    def test_scan_document_package_ok(self):
        self._test_scan_ok(lambda picking: picking.move_line_ids.package_id.name)

    def test_scan_document_product_ok(self):
        self._test_scan_ok(
            lambda picking: picking.move_line_ids.product_id[0].barcode,
            in_package=False,
        )

    def test_scan_document_packaging_ok(self):
        self._test_scan_ok(
            lambda picking: picking.move_line_ids.product_id[0].packaging_ids.barcode,
            in_package=False,
        )

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

    def test_scan_document_recover(self):
        """If the user starts to process a line, and for whatever reason he
        stops there and restarts the scenario from the beginning, he should
        still be able to find the previous line.
        """
        picking = self._create_picking()
        self._fill_stock_for_moves(picking.move_lines, in_package=True)
        picking.action_assign()
        package = picking.move_line_ids.package_id
        # The user selects a line, then stops working in the middle of the process
        response = self.service.dispatch(
            "scan_document", params={"barcode": package.name}
        )
        data = response["data"]["select_line"]
        self.assertEqual(data["picking"]["move_line_count"], 2)
        self.assertEqual(len(data["picking"]["move_lines"]), 2)
        self.assertFalse(picking.move_line_ids.shopfloor_user_id)
        response = self.service.dispatch(
            "select_line",
            params={"picking_id": picking.id, "package_id": package.id},
        )
        self.assertTrue(all(m.qty_done for m in picking.move_line_ids))
        self.assertEqual(picking.move_line_ids.shopfloor_user_id, self.env.user)
        # He restarts the scenario and try to select again the previous line
        # to continue its job
        response = self.service.dispatch(
            "scan_document", params={"barcode": package.name}
        )
        data = response["data"]["select_line"]
        self.assertEqual(data["picking"]["move_line_count"], 2)
        self.assertEqual(len(data["picking"]["move_lines"]), 2)  # Lines found
