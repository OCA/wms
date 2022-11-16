# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from .test_zone_picking_base import ZonePickingCommonCase


class ZonePickingSetLineDestinationCase(ZonePickingCommonCase):
    """Tests for endpoint used from set_line_destination

    * /set_destination

    """

    def setUp(self):
        super().setUp()
        self.service.work.current_picking_type = self.picking1.picking_type_id

    def test_set_destination_wrong_parameters(self):
        move_line = self.picking1.move_line_ids[0]
        response = self.service.dispatch(
            "set_destination",
            params={
                "move_line_id": 1234567890,
                "barcode": self.packing_location.barcode,
                "quantity": move_line.product_uom_qty,
                "confirmation": False,
            },
        )
        self.assert_response_start(
            response,
            message=self.service.msg_store.record_not_found(),
        )

    def test_set_destination_location_confirm(self):
        """Scanned barcode is the destination location but needs confirmation
        as it is outside the current move line destination but is still
        allowed by the picking type's default destination.
        """
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        move_line = self.picking1.move_line_ids
        move_line.location_dest_id = self.shelf1
        quantity_done = move_line.product_uom_qty
        response = self.service.dispatch(
            "set_destination",
            params={
                "move_line_id": move_line.id,
                "barcode": self.packing_location.barcode,
                "quantity": quantity_done,
                "confirmation": False,
            },
        )
        # Check response
        self.assert_response_set_line_destination(
            response,
            zone_location,
            picking_type,
            move_line,
            message=self.service.msg_store.confirm_location_changed(
                move_line.location_dest_id, self.packing_location
            ),
            confirmation_required=True,
            qty_done=quantity_done,
        )
        # Confirm the destination with a wrong destination (should not happen)
        response = self.service.dispatch(
            "set_destination",
            params={
                "move_line_id": move_line.id,
                "barcode": self.customer_location.barcode,
                "quantity": move_line.product_uom_qty,
                "confirmation": True,
            },
        )
        # Check response
        self.assert_response_set_line_destination(
            response,
            zone_location,
            picking_type,
            move_line,
            message=self.service.msg_store.dest_location_not_allowed(),
            qty_done=quantity_done,
        )
        # Confirm the destination with the right destination this time
        response = self.service.dispatch(
            "set_destination",
            params={
                "move_line_id": move_line.id,
                "barcode": self.packing_location.barcode,
                "quantity": move_line.product_uom_qty,
                "confirmation": True,
            },
        )
        # Check response
        move_lines = self.service._find_location_move_lines()
        move_lines = move_lines.sorted(lambda l: l.move_id.priority, reverse=True)
        self.assert_response_select_line(
            response,
            zone_location,
            picking_type,
            move_lines,
            message=self.service.msg_store.confirm_pack_moved(),
        )

    def test_set_destination_location_move_invalid_location(self):
        # Confirm the destination with a wrong destination, outside of picking
        # and move's move line (should not happen)
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        move_line = self.picking1.move_line_ids
        move_line.move_id.location_dest_id = self.packing_sublocation_a
        move_line.picking_id.location_dest_id = self.packing_sublocation_a
        quantity_done = move_line.product_uom_qty
        response = self.service.dispatch(
            "set_destination",
            params={
                "move_line_id": move_line.id,
                "barcode": self.packing_sublocation_b.barcode,
                "quantity": quantity_done,
                "confirmation": True,
            },
        )
        # Check response
        self.assert_response_set_line_destination(
            response,
            zone_location,
            picking_type,
            move_line,
            message=self.service.msg_store.dest_location_not_allowed(),
            qty_done=quantity_done,
        )

    def test_set_destination_location_no_other_move_line_full_qty(self):
        """Scanned barcode is the destination location.

        The move line is the only one in the move, and we move the whole qty.

        Initial data:

            move qty 10 (assigned):
                -> move_line qty 10 from location X

        Then the operator move the 10 qty, we get:

            move qty 10 (done):
                -> move_line qty 10 from location X
        """
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        moves_before = self.picking1.move_lines
        self.assertEqual(len(moves_before), 1)
        self.assertEqual(len(moves_before.move_line_ids), 1)
        move_line = moves_before.move_line_ids
        response = self.service.dispatch(
            "set_destination",
            params={
                "move_line_id": move_line.id,
                "barcode": self.packing_location.barcode,
                "quantity": move_line.product_uom_qty,
                "confirmation": False,
            },
        )
        self.assertEqual(move_line.state, "done")
        # Check picking data
        moves_after = self.picking1.move_lines
        self.assertEqual(moves_before, moves_after)
        self.assertEqual(move_line.qty_done, 10)
        # Check response
        move_lines = self.service._find_location_move_lines()
        move_lines = move_lines.sorted(lambda l: l.move_id.priority, reverse=True)
        self.assert_response_select_line(
            response,
            zone_location,
            picking_type,
            move_lines,
            message=self.service.msg_store.confirm_pack_moved(),
        )

    def test_set_destination_location_no_other_move_line_partial_qty(self):
        """Scanned barcode is the destination location.

        The move line is the only one in the move, and we move some of the qty.

        Initial data:

            move qty 10 (assigned):
                -> move_line qty 10 from location X

        Then the operator move 6 qty on 10, we get:

            an error because we can move only full qty by location
            and only a package barcode is allowed on scan.
        """
        zone_location = self.zone_location
        picking_type = self.picking3.picking_type_id
        barcode = self.packing_location.barcode
        moves_before = self.picking3.move_lines
        self.assertEqual(len(moves_before), 1)
        self.assertEqual(len(moves_before.move_line_ids), 1)
        move_line = moves_before.move_line_ids
        # we need a destination package if we want to scan a destination location
        move_line.result_package_id = self.free_package
        response = self.service.dispatch(
            "set_destination",
            params={
                "move_line_id": move_line.id,
                "barcode": barcode,
                "quantity": 6,
                "confirmation": False,
            },
        )
        self.assert_response_set_line_destination(
            response,
            zone_location,
            picking_type,
            move_line,
            qty_done=6,
            message=self.service.msg_store.package_not_found_for_barcode(barcode),
        )

    def test_set_destination_location_several_move_line_full_qty(self):
        """Scanned barcode is the destination location.

        The move line has siblings in the move, and we move the whole qty:
        the processed move line will then get its own move (split from original one)

        Initial data:

            move qty 10 (assigned):
                -> move_line qty 6 from location X
                -> move_line qty 4 from location Y

        Then the operator move 6 qty (from the first move line), we get:

            move qty 6 (done):
                -> move_line qty 4 from location X
            move qty 4 (assigned):
                -> move_line qty 4 from location Y (untouched)
        """
        zone_location = self.zone_location
        picking_type = self.picking4.picking_type_id
        moves_before = self.picking4.move_lines
        self.assertEqual(len(moves_before), 1)
        self.assertEqual(len(moves_before.move_line_ids), 2)
        move_line = moves_before.move_line_ids[0]
        # we need a destination package if we want to scan a destination location
        move_line.result_package_id = self.free_package
        other_move_line = moves_before.move_line_ids[1]
        response = self.service.dispatch(
            "set_destination",
            params={
                "move_line_id": move_line.id,
                "barcode": self.packing_location.barcode,
                "quantity": move_line.product_uom_qty,  # 6 qty
                "confirmation": False,
            },
        )
        self.assertEqual(move_line.state, "done")
        # Check picking data (move has been split in two, 6 done and 4 remaining)

        done_picking = self.picking4.backorder_ids
        self.assertEqual(done_picking.state, "done")
        self.assertEqual(self.picking4.state, "assigned")
        move_after = self.picking4.move_lines
        self.assertEqual(len(move_after), 1)
        self.assertEqual(move_line.move_id.product_uom_qty, 6)
        self.assertEqual(move_line.move_id.state, "done")
        self.assertEqual(move_line.move_id.move_line_ids.product_uom_qty, 0)
        self.assertEqual(move_after.product_uom_qty, 4)
        self.assertEqual(move_after.state, "assigned")
        self.assertEqual(move_after.move_line_ids.product_uom_qty, 4)
        self.assertEqual(move_line.qty_done, 6)
        self.assertNotEqual(move_line.move_id, other_move_line.move_id)
        # Check response
        move_lines = self.service._find_location_move_lines()
        move_lines = move_lines.sorted(lambda l: l.move_id.priority, reverse=True)
        self.assert_response_select_line(
            response,
            zone_location,
            picking_type,
            move_lines,
            message=self.service.msg_store.confirm_pack_moved(),
        )

    def test_set_destination_location_several_move_line_partial_qty(self):
        """Scanned barcode is the destination location.

        The move line has siblings in the move, and we move some of the qty:
        the processed move line will then get its own move (split from original one)

        Initial data:

            move qty 10 (assigned):
                -> move_line qty 6 from location X
                -> move_line qty 4 from location Y

        Then the operator move 4 qty on 6 (from the first move line), we get:

            an error because we can move only full qty by location
            and only a package barcode is allowed on scan.
        """
        zone_location = self.zone_location
        picking_type = self.picking4.picking_type_id
        barcode = self.packing_location.barcode
        moves_before = self.picking4.move_lines
        self.assertEqual(len(moves_before), 1)  # 10 qty
        self.assertEqual(len(moves_before.move_line_ids), 2)  # 6+4 qty
        move_line = moves_before.move_line_ids[0]
        # we need a destination package if we want to scan a destination location
        move_line.result_package_id = self.free_package
        response = self.service.dispatch(
            "set_destination",
            params={
                "move_line_id": move_line.id,
                "barcode": barcode,
                "quantity": 4,  # 4/6 qty
                "confirmation": False,
            },
        )
        self.assert_response_set_line_destination(
            response,
            zone_location,
            picking_type,
            move_line,
            qty_done=4,
            message=self.service.msg_store.package_not_found_for_barcode(barcode),
        )

    def test_set_destination_location_zero_check(self):
        """Scanned barcode is the destination location.

        The move line is the only one in the source location, as such the
        'zero_check' step is triggered.
        """
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        picking_type.sudo().shopfloor_zero_check = True
        self.assertEqual(len(self.picking1.move_line_ids), 1)
        move_line = self.picking1.move_line_ids
        location_is_empty = move_line.location_id.planned_qty_in_location_is_empty
        self.assertFalse(location_is_empty())
        response = self.service.dispatch(
            "set_destination",
            params={
                "move_line_id": move_line.id,
                "barcode": self.packing_location.barcode,
                "quantity": move_line.product_uom_qty,
                "confirmation": False,
            },
        )
        self.assertTrue(location_is_empty())
        # Check response
        self.assert_response_zero_check(
            response, zone_location, picking_type, move_line
        )

    def test_set_destination_package_full_qty(self):
        """Scanned barcode is the destination package.

        Initial data:

            move qty 10 (assigned):
                -> move_line qty 10 from location X

        Then the operator move the 10 qty, we get:

            move qty 10 (done):
                -> move_line qty 10 from location X with the scanned package
        """
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        moves_before = self.picking1.move_lines
        self.assertEqual(len(moves_before), 1)
        self.assertEqual(len(moves_before.move_line_ids), 1)
        move_line = moves_before.move_line_ids
        response = self.service.dispatch(
            "set_destination",
            params={
                "move_line_id": move_line.id,
                "barcode": self.free_package.name,
                "quantity": move_line.product_uom_qty,
                "confirmation": False,
            },
        )
        # Check picking data
        moves_after = self.picking1.move_lines
        self.assertEqual(moves_before, moves_after)
        self.assertRecordValues(
            move_line,
            [
                {
                    "result_package_id": self.free_package.id,
                    "product_uom_qty": 10,
                    "qty_done": 10,
                    "shopfloor_user_id": self.env.user.id,
                },
            ],
        )
        # Check response
        move_lines = self.service._find_location_move_lines()
        move_lines = move_lines.sorted(lambda l: l.move_id.priority, reverse=True)
        self.assert_response_select_line(
            response,
            zone_location,
            picking_type,
            move_lines,
            message=self.service.msg_store.confirm_pack_moved(),
        )

    def test_set_destination_package_partial_qty(self):
        """Scanned barcode is the destination package.

        Initial data:

            move qty 10 (assigned):
                -> move_line qty 10 from location X

        Then the operator move the 6 on 10 qty, we get:

            move qty 6 (assigned):
                -> move_line qty 6 from location X with the scanned package (buffer)
                -> move_line qty 4 from location X (remaining)
        """
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        moves_before = self.picking1.move_lines
        self.assertEqual(len(moves_before), 1)
        self.assertEqual(len(moves_before.move_line_ids), 1)
        move_line = moves_before.move_line_ids
        response = self.service.dispatch(
            "set_destination",
            params={
                "move_line_id": move_line.id,
                "barcode": self.free_package.name,
                "quantity": 6,
                "confirmation": False,
            },
        )
        # Check picking data
        moves_after = self.picking1.move_lines
        new_move_line = self.picking1.move_line_ids.filtered(
            lambda line: line != move_line
        )
        self.assertTrue(move_line != new_move_line)
        self.assertEqual(moves_before, moves_after)
        self.assertRecordValues(
            move_line,
            [
                {
                    "result_package_id": self.free_package.id,
                    "product_uom_qty": 6,
                    "qty_done": 6,
                    "shopfloor_user_id": self.env.user.id,
                },
            ],
        )
        self.assertRecordValues(
            new_move_line,
            [
                {
                    "result_package_id": new_move_line.package_id.id,  # Unchanged
                    "product_uom_qty": 4,
                    "qty_done": 0,
                    "shopfloor_user_id": False,
                },
            ],
        )
        # Check response
        move_lines = self.service._find_location_move_lines()
        move_lines = move_lines.sorted(lambda l: l.move_id.priority, reverse=True)
        self.assert_response_select_line(
            response,
            zone_location,
            picking_type,
            move_lines,
            message=self.service.msg_store.confirm_pack_moved(),
        )

    def test_set_destination_package_zero_check(self):
        """Scanned barcode is the destination package.

        The move line is the only one in the source location, as such the
        'zero_check' step is triggered.
        """
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        picking_type.sudo().shopfloor_zero_check = True
        self.assertEqual(len(self.picking1.move_line_ids), 1)
        move_line = self.picking1.move_line_ids
        location_is_empty = move_line.location_id.planned_qty_in_location_is_empty
        self.assertFalse(location_is_empty())
        response = self.service.dispatch(
            "set_destination",
            params={
                "move_line_id": move_line.id,
                "barcode": self.free_package.name,
                "quantity": move_line.product_uom_qty,
                "confirmation": False,
            },
        )
        self.assertTrue(location_is_empty())
        # Check response
        self.assert_response_zero_check(
            response,
            zone_location,
            picking_type,
            move_line,
        )

    def test_set_same_destination_package_multiple_moves(self):
        """Scanned barcode is the destination package."""
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        # picking_type.sudo().shopfloor_zero_check = True
        self.assertEqual(len(self.picking1.move_line_ids), 1)
        move_line = self.picking1.move_line_ids
        location_is_empty = move_line.location_id.planned_qty_in_location_is_empty
        self.assertFalse(location_is_empty())
        response = self.service.dispatch(
            "set_destination",
            params={
                "move_line_id": move_line.id,
                "barcode": self.free_package.name,
                "quantity": move_line.product_uom_qty,
                "confirmation": False,
            },
        )
        self.assertTrue(location_is_empty())
        # Check response
        move_lines = self.service._find_location_move_lines()
        move_lines = move_lines.sorted(lambda l: l.move_id.priority, reverse=True)
        self.assert_response_select_line(
            response,
            zone_location,
            picking_type,
            move_lines,
            message=self.service.msg_store.confirm_pack_moved(),
        )
        # Now, try to add more goods in the same package
        move_line = self.picking3.move_line_ids
        response = self.service.dispatch(
            "set_destination",
            params={
                "move_line_id": move_line.id,
                "barcode": self.free_package.name,
                "quantity": move_line.product_uom_qty,
                "confirmation": False,
            },
        )
        self.assertEqual(
            response["message"],
            {
                "body": "Package FREE_PACKAGE is already used.",
                "message_type": "warning",
            },
        )
        # Now enable `multiple_move_single_pack` and try again
        self.menu.sudo().write(
            {
                "multiple_move_single_pack": True,
                "unload_package_at_destination": True,
            }
        )
        response = self.service.dispatch(
            "set_destination",
            params={
                "move_line_id": move_line.id,
                "barcode": self.free_package.name,
                "quantity": move_line.product_uom_qty,
                "confirmation": False,
            },
        )
        # We now have no error in the response
        move_lines = self.service._find_location_move_lines()
        move_lines = move_lines.sorted(lambda l: l.move_id.priority, reverse=True)
        self.assert_response_select_line(
            response,
            zone_location,
            picking_type,
            move_lines,
            message=self.service.msg_store.confirm_pack_moved(),
        )
