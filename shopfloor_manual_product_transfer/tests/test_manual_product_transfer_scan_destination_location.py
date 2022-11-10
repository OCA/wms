# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from .test_manual_product_transfer_base import ManualProductTransferCommonCase


class ManualProductTransferScanDestinationLocation(ManualProductTransferCommonCase):
    """Tests for confirm_quantity state

    Endpoints:

    * /scan_destination_location
    * /cancel
    """

    def test_scan_destination_location_wrong_picking_id(self):
        response = self.service.dispatch(
            "scan_destination_location",
            params={"move_line_ids": [-1], "barcode": self.shelf1.barcode},
        )
        self.assert_response_start(
            response,
            message=self.service.msg_store.record_not_found(),
        )

    def _confirm_quantity(self):
        self.service.dispatch(
            "confirm_quantity",
            params={
                "location_id": self.src_location.id,
                "product_id": self.product_a.id,
                "quantity": 10,
                "confirm": True,
            },
        )
        move_lines = self.service._find_user_move_lines(
            self.src_location, self.product_a
        )
        picking = move_lines.picking_id
        return picking, move_lines

    def test_scan_destination_location_wrong_destination(self):
        picking, move_lines = self._confirm_quantity()
        response = self.service.dispatch(
            "scan_destination_location",
            params={
                "move_line_ids": move_lines.ids,
                "barcode": self.not_allowed_location.barcode,
            },
        )
        self.assertEqual(move_lines.state, "assigned")
        self.assert_response_scan_destination_location(
            response,
            picking,
            move_lines,
            message=self.service.msg_store.location_not_allowed(),
        )

    def test_scan_destination_location_ok(self):
        picking, move_lines = self._confirm_quantity()
        response = self.service.dispatch(
            "scan_destination_location",
            params={"move_line_ids": move_lines.ids, "barcode": self.shelf1.barcode},
        )
        self.assertEqual(move_lines.state, "done")
        self.assert_response_start(
            response, message=self.service.msg_store.transfer_done_success(picking)
        )

    def test_cancel_ok(self):
        picking, move_lines = self._confirm_quantity()
        response = self.service.dispatch(
            "cancel",
            params={"move_line_ids": move_lines.ids},
        )
        self.assertEqual(move_lines.state, "cancel")
        self.assert_response_start(
            response, message=self.service.msg_store.transfer_canceled_success(picking)
        )
