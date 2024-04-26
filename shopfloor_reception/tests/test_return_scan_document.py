# Copyright 2023 Camptocamp SA
# Copyright 2024 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from .reception_return_common import CommonCaseReturn


class TestScanDocumentReturn(CommonCaseReturn):
    def test_scan_wrong_barcode(self):
        # Same test as in shopfloor_delivery, to ensure this module doesn't break
        # the base behaviour
        self._enable_allow_return()
        self.create_delivery()
        response = self.service.dispatch("scan_document", params={"barcode": "NOPE"})
        self.assert_response(
            response,
            next_state="select_document",
            data={"pickings": []},
            message={"message_type": "error", "body": "Barcode not found"},
        )

    def test_scan_document_no_default_location(self):
        # Remove default locations on picking type.
        # Ensure an error message is returned in such case.
        self.picking_type.sudo().write(
            {"default_location_src_id": False, "default_location_dest_id": False}
        )
        self._enable_allow_return()
        delivery = self.create_delivery()
        self.deliver(delivery)
        response = self.service.dispatch(
            "scan_document", params={"barcode": self.order.name}
        )
        return_picking = self.get_new_pickings()
        self.assertFalse(return_picking)
        message = {
            "message_type": "error",
            "body": (
                "Operation types for this menu are missing "
                "default source and destination locations."
            ),
        }
        self.assert_response(
            response,
            next_state="select_document",
            data={"pickings": []},
            message=message,
        )

    def test_scan_undelivered_order(self):
        # An order has been created and confirmed, but hasn't been delivered yet.
        # Therefore, delivery isn't done, and using SO name as input should return
        # a "barcode not found" error
        self._enable_allow_return()
        self.create_delivery()
        response = self.service.dispatch(
            "scan_document", params={"barcode": self.order.name}
        )
        self.assert_response(
            response,
            next_state="select_document",
            data={"pickings": []},
            message={
                "message_type": "error",
                "body": "Barcode not found",
            },
        )

    def test_scan_delivered_order(self):
        # Order has been delivered.
        # Now, the SO name can be used as an input on the `scan_document` to create
        # a return.
        delivery = self.create_delivery()
        self.deliver(delivery)
        # First try, `allow_return` is disabled, we should get a barcode error
        response = self.service.dispatch(
            "scan_document", params={"barcode": self.order.name}
        )
        self.assert_response(
            response,
            next_state="select_document",
            data={"pickings": []},
            message={"message_type": "error", "body": "Barcode not found"},
        )
        # Now, enable `allow_return`
        self._enable_allow_return()
        response = self.service.dispatch(
            "scan_document", params={"barcode": self.order.name}
        )
        return_picking = self.get_new_pickings()
        self.assert_return_of(return_picking, self.order.name)
        self.assert_response(
            response,
            next_state="select_move",
            data={"picking": self._data_for_picking_with_moves(return_picking)},
        )

    def test_scan_partial_delivered_order(self):
        # Order has been partial delivered.
        # Now, the SO name can be used as an input on the `scan_document` to create
        # a return.
        self._enable_allow_return()
        delivery = self.create_delivery()
        backorder = self.partial_deliver(delivery, 10)
        self.assertEqual(backorder.move_lines.product_qty, 10)
        response = self.service.dispatch(
            "scan_document", params={"barcode": self.order.name}
        )
        return_picking = self.get_new_pickings() - backorder
        self.assert_return_of(return_picking, self.order.name)
        self.assert_response(
            response,
            next_state="select_move",
            data={"picking": self._data_for_picking_with_moves(return_picking)},
        )
