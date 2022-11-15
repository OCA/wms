# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from .test_manual_product_transfer_base import ManualProductTransferCommonCase


class ManualProductTransferScanProduct(ManualProductTransferCommonCase):
    """Tests for scan_product state

    Endpoints:

    * /scan_product
    """

    def test_scan_product_not_found_error(self):
        response = self.service.dispatch(
            "scan_product",
            params={"location_id": self.src_location.id, "barcode": "UNKNOWN"},
        )
        self.assert_response_scan_product(
            response,
            self.src_location,
            message=self.service.msg_store.barcode_not_found(),
        )

    def test_scan_product_tracked_by_lot_error(self):
        response = self.service.dispatch(
            "scan_product",
            params={
                "location_id": self.src_location.id,
                "barcode": self.product_b.barcode,
            },
        )
        self.assert_response_scan_product(
            response,
            self.src_location,
            message=self.service.msg_store.scan_lot_on_product_tracked_by_lot(),
        )

    def test_scan_product_product_ok(self):
        response = self.service.dispatch(
            "scan_product",
            params={
                "location_id": self.src_location.id,
                "barcode": self.product_a.barcode,
            },
        )
        self.assert_response_confirm_quantity(
            response,
            self.src_location,
            self.product_a,
            10,
        )

    def test_scan_product_product_reserved_warning_ok(self):
        # initial qty is 10, but we reserve 2 qties (so 8 fully free)
        picking = self._create_picking(
            picking_type=self.env.ref("stock.picking_type_out"),
            lines=[(self.product_a, 2)],
            confirm=True,
        )
        picking.action_assign()
        response = self.service.dispatch(
            "scan_product",
            params={
                "location_id": self.src_location.id,
                "barcode": self.product_a.barcode,
            },
        )
        self.assert_response_confirm_quantity(
            response,
            self.src_location,
            self.product_a,
            quantity=8,
            warning=self.service.msg_store.qty_assigned_to_preserve(
                self.product_a, 2.0
            )["body"],
        )

    def test_scan_product_lot_ok(self):
        response = self.service.dispatch(
            "scan_product",
            params={
                "location_id": self.src_location.id,
                "barcode": self.product_b_lot.name,
            },
        )
        self.assert_response_confirm_quantity(
            response,
            self.src_location,
            self.product_b,
            10,
            self.product_b_lot,
        )

    def test_scan_product_recover_session(self):
        # create a move and its move lines by confirming qty
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
        # check we are redirected to the "scan_destination_location" state
        # when scanning the same product
        response = self.service.dispatch(
            "scan_product",
            params={
                "location_id": self.src_location.id,
                "barcode": self.product_a.barcode,
            },
        )
        self.assert_response_scan_destination_location(
            response,
            move_lines.picking_id,
            move_lines,
            message=self.service.msg_store.recovered_previous_session(),
        )
