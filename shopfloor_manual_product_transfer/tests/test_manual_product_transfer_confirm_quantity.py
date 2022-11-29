# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from .test_manual_product_transfer_base import ManualProductTransferCommonCase


class ManualProductTransferConfirmQuantity(ManualProductTransferCommonCase):
    """Tests for confirm_quantity state

    Endpoints:

    * /confirm_quantity
    * /set_quantity
    """

    def test_confirm_quantity_wrong_product_barcode(self):
        barcode = "UNKNOWN"
        response = self.service.dispatch(
            "confirm_quantity",
            params={
                "location_id": self.src_location.id,
                "product_id": self.product_a.id,
                "quantity": 10,
                "barcode": barcode,
            },
        )
        self.assert_response_confirm_quantity(
            response,
            self.src_location,
            self.product_a,
            10,
            message=self.service.msg_store.no_product_for_barcode(barcode),
        )

    def test_confirm_quantity_wrong_lot_barcode(self):
        barcode = "UNKNOWN"
        response = self.service.dispatch(
            "confirm_quantity",
            params={
                "location_id": self.src_location.id,
                "product_id": self.product_b.id,
                "quantity": 10,
                "lot_id": self.product_b_lot.id,
                "barcode": barcode,
            },
        )
        self.assert_response_confirm_quantity(
            response,
            self.src_location,
            self.product_b,
            10,
            self.product_b_lot,
            message=self.service.msg_store.no_lot_for_barcode(barcode),
        )

    def test_confirm_quantity_product_barcode_ok(self):
        barcode = self.product_a.barcode
        response = self.service.dispatch(
            "confirm_quantity",
            params={
                "location_id": self.src_location.id,
                "product_id": self.product_a.id,
                "quantity": 10,
                "barcode": barcode,
            },
        )
        move_lines = self.service._find_user_move_lines(
            self.src_location, self.product_a
        )
        self.assert_response_scan_destination_location(
            response, move_lines.picking_id, move_lines
        )

    def test_confirm_quantity_product_confirm_ok(self):
        response = self.service.dispatch(
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
        self.assert_response_scan_destination_location(
            response, move_lines.picking_id, move_lines
        )

    def test_confirm_quantity_lot_barcode_ok(self):
        barcode = self.product_b_lot.name
        response = self.service.dispatch(
            "confirm_quantity",
            params={
                "location_id": self.src_location.id,
                "product_id": self.product_b.id,
                "quantity": 10,
                "lot_id": self.product_b_lot.id,
                "barcode": barcode,
            },
        )
        move_lines = self.service._find_user_move_lines(
            self.src_location, self.product_b, self.product_b_lot
        )
        self.assertEqual(move_lines.lot_id, self.product_b_lot)
        self.assert_response_scan_destination_location(
            response, move_lines.picking_id, move_lines
        )

    def test_confirm_quantity_lot_confirm_ok(self):
        response = self.service.dispatch(
            "confirm_quantity",
            params={
                "location_id": self.src_location.id,
                "product_id": self.product_b.id,
                "quantity": 10,
                "lot_id": self.product_b_lot.id,
                "confirm": True,
            },
        )
        move_lines = self.service._find_user_move_lines(
            self.src_location, self.product_b, self.product_b_lot
        )
        self.assertEqual(move_lines.lot_id, self.product_b_lot)
        self.assert_response_scan_destination_location(
            response, move_lines.picking_id, move_lines
        )

    def test_confirm_quantity_with_unreservation_disabled(self):
        self.menu.sudo().allow_unreserve_other_moves = False
        # initial qty is 10, but we reserve 2 qties (so 8 fully free)
        picking = self._create_picking(
            picking_type=self.env.ref("stock.picking_type_out"),
            lines=[(self.product_a, 2)],
            confirm=True,
        )
        picking.action_assign()
        # confirm 9 qties to process (more than 8)
        response = self.service.dispatch(
            "confirm_quantity",
            params={
                "location_id": self.src_location.id,
                "product_id": self.product_a.id,
                "quantity": 9,
                "confirm": True,
            },
        )
        # we get:
        #   - a warning saying that 2 reserved qties should not be taken
        #   - an error message and the quantity to move is reset to 8
        self.assert_response_confirm_quantity(
            response,
            self.src_location,
            self.product_a,
            quantity=8,
            warning=self.service.msg_store.qty_assigned_to_preserve(
                self.product_a, 2.0
            )["body"],
            message=self.service.msg_store.qty_exceeds_initial_qty(),
        )
        move_lines = self.service._find_user_move_lines(
            self.src_location, self.product_a
        )
        self.assertFalse(move_lines)

    def test_confirm_quantity_with_unreservation_enabled(self):
        self.menu.sudo().allow_unreserve_other_moves = True
        # initial qty is 10, but we reserve 2 qties (so 8 fully free)
        picking = self._create_picking(
            picking_type=self.env.ref("stock.picking_type_out"),
            lines=[(self.product_a, 2)],
            confirm=True,
        )
        picking.action_assign()
        # confirm 9 qties to process (more than 8)
        response = self.service.dispatch(
            "confirm_quantity",
            params={
                "location_id": self.src_location.id,
                "product_id": self.product_a.id,
                "quantity": 9,
                "confirm": True,
            },
        )
        # the existing move lines has been unreserve to satisfy the move of 9
        # qties to process
        self.assertRecordValues(
            picking.move_lines,
            [
                {
                    "state": "partially_available",
                    "product_uom_qty": 2,
                    "reserved_availability": 1,
                },
            ],
        )
        move_lines = self.service._find_user_move_lines(
            self.src_location, self.product_a
        )
        self.assertRecordValues(
            move_lines, [{"state": "assigned", "product_uom_qty": 9, "qty_done": 9}]
        )
        self.assert_response_scan_destination_location(
            response, move_lines.picking_id, move_lines
        )

    def test_confirm_quantity_with_unreservation_enabled_and_picking_started(self):
        self.menu.sudo().allow_unreserve_other_moves = True
        # initial qty is 10, but we reserve 2 qties (so 8 fully free)
        picking = self._create_picking(
            picking_type=self.env.ref("stock.picking_type_out"),
            lines=[(self.product_a, 2)],
            confirm=True,
        )
        picking.action_assign()
        # another transfer with 2 qties reserved and some done (so 6 fully free)
        picking2 = self._create_picking(
            picking_type=self.env.ref("stock.picking_type_out"),
            lines=[(self.product_a, 2)],
            confirm=True,
        )
        picking2.action_assign()
        picking2.move_line_ids.qty_done = 1

        # confirm 7 qties to process (more than 6)
        response = self.service.dispatch(
            "confirm_quantity",
            params={
                "location_id": self.src_location.id,
                "product_id": self.product_a.id,
                "quantity": 9,
                "confirm": True,
            },
        )
        self.assert_response_start(
            response,
            message=self.service.msg_store.picking_already_started_in_location(
                picking2
            ),
        )

    def test_confirm_quantity_exceeds_initial_qty(self):
        # initial qty is 10, but we try to process 11
        response = self.service.dispatch(
            "confirm_quantity",
            params={
                "location_id": self.src_location.id,
                "product_id": self.product_a.id,
                "quantity": 11,
                "confirm": True,
            },
        )
        self.assert_response_confirm_quantity(
            response,
            self.src_location,
            self.product_a,
            10,
            message=self.service.msg_store.qty_exceeds_initial_qty(),
        )

    def test_confirm_quantity_with_putaway_destination_required_error(self):
        self.menu.sudo().ignore_no_putaway_available = True
        response = self.service.dispatch(
            "confirm_quantity",
            params={
                "location_id": self.src_location.id,
                "product_id": self.product_a.id,
                "quantity": 10,
                "confirm": True,
            },
        )
        self.assert_response_confirm_quantity(
            response,
            self.src_location,
            self.product_a,
            10,
            message=self.service.msg_store.no_putaway_destination_available(),
        )

    def test_set_quantity_ok(self):
        # initial qty is 10
        response = self.service.dispatch(
            "set_quantity",
            params={
                "location_id": self.src_location.id,
                "product_id": self.product_a.id,
                "quantity": 9,
            },
        )
        self.assert_response_confirm_quantity(
            response,
            self.src_location,
            self.product_a,
            9,
        )

    def test_set_quantity_exceeds_initial_qty(self):
        # initial qty is 10
        response = self.service.dispatch(
            "set_quantity",
            params={
                "location_id": self.src_location.id,
                "product_id": self.product_a.id,
                "quantity": 11,
            },
        )
        self.assert_response_confirm_quantity(
            response,
            self.src_location,
            self.product_a,
            10,
            message=self.service.msg_store.qty_exceeds_initial_qty(),
        )
