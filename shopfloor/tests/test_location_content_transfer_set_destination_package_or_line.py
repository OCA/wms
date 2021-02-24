# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from .test_location_content_transfer_base import LocationContentTransferCommonCase


class LocationContentTransferSetDestinationXCase(LocationContentTransferCommonCase):
    """Tests for endpoint used from scan_destination

    * /set_destination_package
    * /set_destination_line

    """

    # TODO see what can be common
    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()
        products = cls.product_a + cls.product_b + cls.product_c + cls.product_d
        for product in products:
            cls.env["stock.putaway.rule"].sudo().create(
                {
                    "product_id": product.id,
                    "location_in_id": cls.stock_location.id,
                    "location_out_id": cls.shelf1.id,
                }
            )

        cls.picking1 = picking1 = cls._create_picking(
            lines=[(cls.product_a, 10), (cls.product_b, 10)]
        )
        cls.picking2 = picking2 = cls._create_picking(
            lines=[(cls.product_c, 10), (cls.product_d, 10)]
        )
        cls.pickings = picking1 | picking2
        cls._fill_stock_for_moves(
            picking1.move_lines, in_package=True, location=cls.content_loc
        )
        cls._fill_stock_for_moves(picking2.move_lines, location=cls.content_loc)
        cls.pickings.action_assign()
        cls._simulate_pickings_selected(cls.pickings)
        cls.dest_location = (
            cls.env["stock.location"]
            .sudo()
            .create(
                {
                    "name": "Sub Shelf 1",
                    "barcode": "subshelf1",
                    "location_id": cls.shelf1.id,
                }
            )
        )

    def test_set_destination_package_wrong_parameters(self):
        """Wrong 'location' and 'package_level_id' parameters, redirect the
        user to the 'start' screen.
        """
        package_level = self.picking1.package_level_ids[0]
        response = self.service.dispatch(
            "set_destination_package",
            params={
                "location_id": 1234567890,  # Doesn't exist
                "package_level_id": package_level.id,
                "barcode": "TEST",
            },
        )
        self.assert_response_start(
            response, message=self.service.msg_store.record_not_found()
        )
        response = self.service.dispatch(
            "set_destination_package",
            params={
                "location_id": self.content_loc.id,
                "package_level_id": 1234567890,  # Doesn't exist
                "barcode": "TEST",
            },
        )
        move_lines = self.service._find_transfer_move_lines(self.content_loc)
        self.assert_response_start_single(
            response, move_lines.mapped("picking_id"),
        )

    def test_set_destination_package_dest_location_nok(self):
        """Scanned destination location not valid, redirect to 'scan_destination'."""
        package_level = self.picking1.package_level_ids[0]
        # Unknown destination location
        response = self.service.dispatch(
            "set_destination_package",
            params={
                "location_id": self.content_loc.id,
                "package_level_id": package_level.id,
                "barcode": "UNKNOWN_LOCATION",
            },
        )
        self.assert_response_scan_destination(
            response, package_level, message=self.service.msg_store.no_location_found(),
        )
        # Destination location not allowed
        customer_location = self.env.ref("stock.stock_location_customers")
        customer_location.sudo().barcode = "CUSTOMER"
        response = self.service.dispatch(
            "set_destination_package",
            params={
                "location_id": self.content_loc.id,
                "package_level_id": package_level.id,
                "barcode": customer_location.barcode,
            },
        )
        self.assert_response_scan_destination(
            response,
            package_level,
            message=self.service.msg_store.dest_location_not_allowed(),
        )

    def test_set_destination_package_dest_location_move_nok(self):
        """Scanned destination location not valid (different as move)"""
        package_level = self.picking1.package_level_ids[0]
        # if the move related to the package level has a destination
        # location not a parent or equal to the scanned location,
        # refuse the action
        move = package_level.move_line_ids.move_id
        move.location_dest_id = self.shelf1
        response = self.service.dispatch(
            "set_destination_package",
            params={
                "location_id": self.content_loc.id,
                "package_level_id": package_level.id,
                "barcode": self.shelf2.barcode,
            },
        )
        self.assert_response_scan_destination(
            response,
            package_level,
            message=self.service.msg_store.dest_location_not_allowed(),
        )

    def test_set_destination_package_dest_location_to_confirm(self):
        """Scanned destination location valid, but need a confirmation."""
        package_level = self.picking1.package_level_ids[0]
        response = self.service.dispatch(
            "set_destination_package",
            params={
                "location_id": self.content_loc.id,
                "package_level_id": package_level.id,
                "barcode": self.env.ref("stock.stock_location_14").barcode,
            },
        )
        self.assert_response_scan_destination(
            response,
            package_level,
            message=self.service.msg_store.need_confirmation(),
            confirmation_required=True,
        )

    def test_set_destination_package_dest_location_ok(self):
        """Scanned destination location valid, moves set to done."""
        original_picking = self.picking1
        package_level = original_picking.package_level_ids[0]
        response = self.service.dispatch(
            "set_destination_package",
            params={
                "location_id": self.content_loc.id,
                "package_level_id": package_level.id,
                "barcode": self.dest_location.barcode,
            },
        )
        # Check the data (the whole transfer has been validated here w/o backorder)
        self.assertFalse(original_picking.backorder_ids)
        self.assertEqual(original_picking.state, "done")
        self.assertEqual(package_level.state, "done")
        # Check the response
        move_lines = self.service._find_transfer_move_lines(self.content_loc)
        self.assert_response_start_single(
            response,
            move_lines.mapped("picking_id"),
            message=self.service.msg_store.location_content_transfer_item_complete(
                self.dest_location
            ),
        )
        for move in package_level.move_line_ids.mapped("move_id"):
            self.assertEqual(move.state, "done")

    def test_set_destination_package_dest_location_ok_with_completion_info(self):
        """Scanned destination location valid, moves set to done
        and completion info is returned as the next transfer is ready.
        """
        original_picking = self.picking1
        package_level = original_picking.package_level_ids[0]
        move = package_level.move_line_ids.move_id[0]
        next_move = move.copy(
            {
                "picking_id": False,
                "location_id": move.location_dest_id.id,
                "location_dest_id": self.customer_location.id,
                "move_orig_ids": [(6, 0, move.ids)],
            }
        )
        next_move._action_confirm(merge=False)
        next_move._assign_picking()
        self.assertEqual(next_move.state, "waiting")
        self.assertTrue(next_move.picking_id)
        response = self.service.dispatch(
            "set_destination_package",
            params={
                "location_id": self.content_loc.id,
                "package_level_id": package_level.id,
                "barcode": self.dest_location.barcode,
            },
        )
        # Check the data (the whole transfer has been validated here w/o backorder)
        self.assertFalse(original_picking.backorder_ids)
        self.assertEqual(original_picking.state, "done")
        self.assertEqual(package_level.state, "done")
        self.assertEqual(next_move.state, "assigned")
        # Check the response
        move_lines = self.service._find_transfer_move_lines(self.content_loc)
        completion_info = self.service._actions_for("completion.info")
        completion_info_popup = completion_info.popup(package_level.move_line_ids)
        self.assert_response_start_single(
            response,
            move_lines.mapped("picking_id"),
            message=self.service.msg_store.location_content_transfer_item_complete(
                self.dest_location
            ),
            popup=completion_info_popup,
        )
        for move in package_level.move_line_ids.mapped("move_id"):
            self.assertEqual(move.state, "done")

    def test_set_destination_line_wrong_parameters(self):
        """Wrong 'location' and 'move_line_id' parameters, redirect the
        user to the 'start' screen.
        """
        move_line = self.picking2.move_line_ids[0]
        response = self.service.dispatch(
            "set_destination_line",
            params={
                "location_id": 1234567890,  # Doesn't exist
                "move_line_id": move_line.id,
                "quantity": move_line.product_uom_qty,
                "barcode": "TEST",
            },
        )
        self.assert_response_start(
            response, message=self.service.msg_store.record_not_found()
        )
        response = self.service.dispatch(
            "set_destination_line",
            params={
                "location_id": self.content_loc.id,
                "move_line_id": 1234567890,  # Doesn't exist
                "quantity": move_line.product_uom_qty,
                "barcode": "TEST",
            },
        )
        move_lines = self.service._find_transfer_move_lines(self.content_loc)
        self.assert_response_start_single(
            response, move_lines.mapped("picking_id"),
        )

    def test_set_destination_line_dest_location_nok(self):
        """Scanned destination location not valid, redirect to 'scan_destination'."""
        move_line = self.picking2.move_line_ids[0]
        # Unknown destination location
        response = self.service.dispatch(
            "set_destination_line",
            params={
                "location_id": self.content_loc.id,
                "move_line_id": move_line.id,
                "quantity": move_line.product_uom_qty,
                "barcode": "UNKNOWN_LOCATION",
            },
        )
        self.assert_response_scan_destination(
            response, move_line, message=self.service.msg_store.no_location_found(),
        )
        # Destination location not allowed
        customer_location = self.env.ref("stock.stock_location_customers")
        customer_location.sudo().barcode = "CUSTOMER"
        response = self.service.dispatch(
            "set_destination_line",
            params={
                "location_id": self.content_loc.id,
                "move_line_id": move_line.id,
                "quantity": move_line.product_uom_qty,
                "barcode": customer_location.barcode,
            },
        )
        self.assert_response_scan_destination(
            response,
            move_line,
            message=self.service.msg_store.dest_location_not_allowed(),
        )

    def test_set_destination_line_dest_location_move_nok(self):
        """Scanned destination location not valid (different as move)"""
        move_line = self.picking2.move_line_ids[0]
        # if the move related to the move line has a destination
        # location not a parent or equal to the scanned location,
        # refuse the action
        move_line.move_id.location_dest_id = self.shelf1
        response = self.service.dispatch(
            "set_destination_line",
            params={
                "location_id": self.content_loc.id,
                "move_line_id": move_line.id,
                "quantity": move_line.product_uom_qty,
                "barcode": self.shelf2.barcode,
            },
        )
        self.assert_response_scan_destination(
            response,
            move_line,
            message=self.service.msg_store.dest_location_not_allowed(),
        )

    def test_set_destination_line_dest_location_to_confirm(self):
        """Scanned destination location valid, but need a confirmation."""
        move_line = self.picking2.move_line_ids[0]
        response = self.service.dispatch(
            "set_destination_line",
            params={
                "location_id": self.content_loc.id,
                "move_line_id": move_line.id,
                "quantity": move_line.product_uom_qty,
                "barcode": self.env.ref("stock.stock_location_14").barcode,
            },
        )
        self.assert_response_scan_destination(
            response,
            move_line,
            message=self.service.msg_store.need_confirmation(),
            confirmation_required=True,
        )

    def test_set_destination_line_dest_location_ok(self):
        """Scanned destination location valid, moves set to done."""
        original_picking = self.picking2
        move_line = original_picking.move_line_ids[0]
        response = self.service.dispatch(
            "set_destination_line",
            params={
                "location_id": self.content_loc.id,
                "move_line_id": move_line.id,
                "quantity": move_line.product_uom_qty,
                "barcode": self.dest_location.barcode,
            },
        )
        # Check the resulting data
        # We got a new picking as the original one had two moves (and we
        # validated only one)
        new_picking = move_line.picking_id
        self.assertTrue(new_picking != original_picking)
        self.assertEqual(move_line.move_id.state, "done")
        self.assertEqual(move_line.picking_id.state, "done")
        self.assertEqual(original_picking.state, "assigned")
        # Check the response
        move_lines = self.service._find_transfer_move_lines(self.content_loc)
        self.assert_response_start_single(
            response,
            move_lines.mapped("picking_id"),
            message=self.service.msg_store.location_content_transfer_item_complete(
                self.dest_location
            ),
        )

    def test_set_destination_line_dest_location_ok_with_completion_info(self):
        """Scanned destination location valid, moves set to done
        and completion info is returned as the next transfer is ready.
        """
        original_picking = self.picking2
        move_line = original_picking.move_line_ids[0]
        move = move_line.move_id
        next_move = move.copy(
            {
                "picking_id": False,
                "location_id": move.location_dest_id.id,
                "location_dest_id": self.customer_location.id,
                "move_orig_ids": [(6, 0, move.ids)],
            }
        )
        next_move._action_confirm(merge=False)
        next_move._assign_picking()
        self.assertEqual(next_move.state, "waiting")
        self.assertTrue(next_move.picking_id)
        response = self.service.dispatch(
            "set_destination_line",
            params={
                "location_id": self.content_loc.id,
                "move_line_id": move_line.id,
                "quantity": move_line.product_uom_qty,
                "barcode": self.dest_location.barcode,
            },
        )
        # Check the resulting data
        # We got a new picking as the original one had two moves (and we
        # validated only one)
        new_picking = move_line.picking_id
        self.assertTrue(new_picking != original_picking)
        self.assertEqual(move_line.move_id.state, "done")
        self.assertEqual(move_line.picking_id.state, "done")
        self.assertEqual(original_picking.state, "assigned")
        self.assertEqual(next_move.state, "assigned")
        # Check the response
        move_lines = self.service._find_transfer_move_lines(self.content_loc)
        completion_info = self.service._actions_for("completion.info")
        completion_info_popup = completion_info.popup(move_line)
        self.assert_response_start_single(
            response,
            move_lines.mapped("picking_id"),
            message=self.service.msg_store.location_content_transfer_item_complete(
                self.dest_location
            ),
            popup=completion_info_popup,
        )

    def test_set_destination_line_partial_qty(self):
        """Scanned destination location with partial qty, but related moves
        has to be splitted.
        """
        original_picking = self.picking2
        move_line_c = original_picking.move_line_ids.filtered(
            lambda m: m.product_id == self.product_c
        )
        move = move_line_c.move_id
        self.assertEqual(move_line_c.product_uom_qty, 10)
        self.assertEqual(move_line_c.qty_done, 10)
        # Scan partial qty (6/10)
        response = self.service.dispatch(
            "set_destination_line",
            params={
                "location_id": self.content_loc.id,
                "move_line_id": move_line_c.id,
                "quantity": move_line_c.product_uom_qty - 4,  # Scan 6 qty
                "barcode": self.dest_location.barcode,
            },
        )
        done_picking = original_picking.backorder_ids
        # Check move line data
        self.assertEqual(move_line_c.move_id.product_uom_qty, 6)
        self.assertEqual(move_line_c.product_uom_qty, 0)
        self.assertEqual(move_line_c.qty_done, 6)
        self.assertEqual(move_line_c.state, "done")
        self.assertEqual(original_picking.backorder_ids, done_picking)
        self.assertEqual(done_picking.state, "done")
        # the move is split with the remaining
        self.assertEqual(original_picking.state, "assigned")
        self.assertEqual(move.state, "assigned")
        self.assertEqual(move.product_id, self.product_c)
        self.assertEqual(move.product_uom_qty, 4)
        self.assertEqual(move.move_line_ids.product_uom_qty, 4)
        self.assertEqual(move.move_line_ids.qty_done, 4)
        # Check the response
        move_lines = self.service._find_transfer_move_lines(self.content_loc)
        self.assert_response_start_single(
            response,
            move_lines.mapped("picking_id"),
            message=self.service.msg_store.location_content_transfer_item_complete(
                self.dest_location
            ),
        )
        self.assertEqual(move_line_c.move_id.state, "done")
        # Scan remaining qty (4/10)
        remaining_move_line_c = move.move_line_ids
        response = self.service.dispatch(
            "set_destination_line",
            params={
                "location_id": self.content_loc.id,
                "move_line_id": remaining_move_line_c.id,
                "quantity": remaining_move_line_c.product_uom_qty,
                "barcode": self.dest_location.barcode,
            },
        )
        done_picking2 = remaining_move_line_c.picking_id
        # Check move line data
        self.assertEqual(remaining_move_line_c.move_id.product_uom_qty, 4)
        self.assertEqual(remaining_move_line_c.product_uom_qty, 0)
        self.assertEqual(remaining_move_line_c.qty_done, 4)
        self.assertEqual(remaining_move_line_c.state, "done")
        self.assertTrue(done_picking2 != original_picking)
        self.assertEqual(done_picking2.state, "done")
        # All move lines related to product_c are now done and extracted from
        # the initial transfer
        all_pickings = original_picking | done_picking | done_picking2
        moves_product_c = all_pickings.move_lines.filtered(
            lambda m: m.product_id == self.product_c
        )
        moves_product_c_done = all(move.state == "done" for move in moves_product_c)
        self.assertTrue(moves_product_c_done)
        moves_product_c_qty_done = sum([move.quantity_done for move in moves_product_c])
        self.assertEqual(moves_product_c_qty_done, 10)
        # The picking is still not done as product_d hasn't been processed
        self.assertEqual(original_picking.state, "assigned")
        # Let scan product_d quantity and check picking state
        move_line_d = original_picking.move_line_ids.filtered(
            lambda m: m.product_id == self.product_d
        )
        response = self.service.dispatch(
            "set_destination_line",
            params={
                "location_id": self.content_loc.id,
                "move_line_id": move_line_d.id,
                "quantity": move_line_d.product_uom_qty,
                "barcode": self.dest_location.barcode,
            },
        )
        self.assertEqual(move_line_d.move_id.product_uom_qty, 10)
        self.assertEqual(move_line_d.product_uom_qty, 0)
        self.assertEqual(move_line_d.qty_done, 10)
        self.assertEqual(move_line_d.state, "done")
        self.assertEqual(original_picking.state, "done")


class LocationContentTransferSetDestinationXSpecialCase(
    LocationContentTransferCommonCase
):
    """Tests for endpoint used from scan_destination (special cases)

    * /set_destination_package
    * /set_destination_line

    """

    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()
        products = cls.product_a
        for product in products:
            cls.env["stock.putaway.rule"].sudo().create(
                {
                    "product_id": product.id,
                    "location_in_id": cls.stock_location.id,
                    "location_out_id": cls.shelf1.id,
                }
            )

        cls.picking = cls._create_picking(
            lines=[(cls.product_a, 10), (cls.product_b, 10)]
        )
        cls.move_product_a = cls.picking.move_lines.filtered(
            lambda m: m.product_id == cls.product_a
        )
        cls.move_product_b = cls.picking.move_lines.filtered(
            lambda m: m.product_id == cls.product_b
        )
        # Change the initial demand of product_a to get two move lines for
        # reserved qties:
        #   - 10 from the package
        #   - 5 from the qty without package
        cls._fill_stock_for_moves(
            cls.move_product_a, in_package=True, location=cls.content_loc
        )
        cls.move_product_a.product_uom_qty = 15
        cls._update_qty_in_location(
            cls.picking.location_id, cls.product_a, 5,
        )
        # Put product_b quantities in two different source locations to get
        # two stock move lines (6 and 4 to satisfy 10 qties)
        cls._update_qty_in_location(cls.picking.location_id, cls.product_b, 6)
        cls._update_qty_in_location(cls.content_loc, cls.product_b, 4)
        # Reserve quantities
        cls.picking.action_assign()
        cls._simulate_pickings_selected(cls.picking)
        cls.dest_location = (
            cls.env["stock.location"]
            .sudo()
            .create(
                {
                    "name": "Sub Shelf 1",
                    "barcode": "subshelf1",
                    "location_id": cls.shelf1.id,
                }
            )
        )

    def test_set_destination_package_split_move(self):
        """Scanned destination location valid for a package, but related moves
        has to be splitted because it is linked to additional move lines.
        """
        original_picking = self.picking
        self.assertEqual(len(original_picking.move_lines), 2)
        self.assertEqual(len(self.move_product_a.move_line_ids), 2)
        package_level = original_picking.package_level_ids[0]
        response = self.service.dispatch(
            "set_destination_package",
            params={
                "location_id": self.content_loc.id,
                "package_level_id": package_level.id,
                "barcode": self.dest_location.barcode,
            },
        )
        done_picking = package_level.picking_id
        # Check the picking data
        self.assertEqual(original_picking.backorder_ids, done_picking)
        self.assertEqual(package_level.location_dest_id, self.dest_location)
        for move_line in package_level.move_line_ids:
            self.assertEqual(move_line.location_dest_id, self.dest_location)
        moves_product_a = original_picking.move_lines.filtered(
            lambda m: m.product_id == self.product_a
        )
        self.assertEqual(len(original_picking.move_lines), 2)
        self.assertEqual(len(moves_product_a), 1)
        for move in moves_product_a:
            self.assertEqual(len(move.move_line_ids), 1)
        move_lines_wo_pkg = original_picking.move_line_ids_without_package
        move_lines_wo_pkg_states = set(move_lines_wo_pkg.mapped("state"))
        self.assertEqual(len(move_lines_wo_pkg_states), 1)
        self.assertEqual(move_lines_wo_pkg_states.pop(), "assigned")
        self.assertEqual(done_picking.package_level_ids.state, "done")
        # Check the response
        move_lines = self.service._find_transfer_move_lines(self.content_loc)
        self.assert_response_start_single(
            response,
            move_lines.mapped("picking_id"),
            message=self.service.msg_store.location_content_transfer_item_complete(
                self.dest_location
            ),
        )

    def test_set_destination_line_split_move(self):
        """Scanned destination location valid for a move line, but related moves
        has to be splitted because it is linked to additional move lines.
        """
        original_picking = self.picking
        self.assertEqual(len(original_picking.move_lines), 2)
        self.assertEqual(len(self.move_product_b.move_line_ids), 2)
        move_line = self.move_product_b.move_line_ids.filtered(
            lambda ml: ml.product_uom_qty == 6
        )
        response = self.service.dispatch(
            "set_destination_line",
            params={
                "location_id": self.content_loc.id,
                "move_line_id": move_line.id,
                "quantity": move_line.product_uom_qty,
                "barcode": self.dest_location.barcode,
            },
        )
        done_picking = move_line.picking_id
        # Check the picking data
        self.assertEqual(original_picking.backorder_ids, done_picking)
        self.assertEqual(done_picking.state, "done")
        self.assertEqual(original_picking.state, "assigned")
        self.assertEqual(move_line.move_id.product_uom_qty, 6)
        self.assertEqual(move_line.product_uom_qty, 0)
        self.assertEqual(move_line.qty_done, 6)
        self.assertEqual(move_line.location_dest_id, self.dest_location)
        self.assertEqual(len(original_picking.move_lines), 2)
        moves_product_b = original_picking.move_lines.filtered(
            lambda m: m.product_id == self.product_b
        )
        self.assertEqual(len(moves_product_b), 1)
        for move in moves_product_b:
            self.assertEqual(len(move.move_line_ids), 1)
        move_lines_wo_pkg = original_picking.move_line_ids_without_package
        move_lines_wo_pkg_states = set(move_lines_wo_pkg.mapped("state"))
        self.assertEqual(len(move_lines_wo_pkg_states), 1)
        self.assertTrue(all(state == "assigned" for state in move_lines_wo_pkg_states))
        self.assertEqual(move_line.state, "done")
        remaining_move = original_picking.move_lines.filtered(
            lambda m: move_line.move_id != m and m.product_id == self.product_b
        )
        self.assertEqual(remaining_move.state, "assigned")
        self.assertEqual(remaining_move.product_uom_qty, 4)
        self.assertEqual(remaining_move.move_line_ids.product_uom_qty, 4)
        self.assertEqual(remaining_move.move_line_ids.qty_done, 4)
        # Check the response
        move_lines = self.service._find_transfer_move_lines(self.content_loc)
        self.assert_response_start_single(
            response,
            move_lines.mapped("picking_id"),
            message=self.service.msg_store.location_content_transfer_item_complete(
                self.dest_location
            ),
        )
        # Process the other move lines (lines w/o package + package levels)
        # to check the picking state
        remaining_move_lines = original_picking.move_line_ids_without_package.filtered(
            lambda ml: ml.state == "assigned"
        )
        for ml in remaining_move_lines:
            self.service.dispatch(
                "set_destination_line",
                params={
                    "location_id": self.content_loc.id,
                    "move_line_id": ml.id,
                    "quantity": ml.product_uom_qty,
                    "barcode": self.dest_location.barcode,
                },
            )
        self.assertEqual(original_picking.state, "assigned")
        package_level = original_picking.package_level_ids[0]
        self.service.dispatch(
            "set_destination_package",
            params={
                "location_id": self.content_loc.id,
                "package_level_id": package_level.id,
                "barcode": self.dest_location.barcode,
            },
        )
        self.assertEqual(original_picking.state, "done")


class LocationContentTransferSetDestinationChainSpecialCase(
    LocationContentTransferCommonCase
):
    """Tests for endpoint used from scan_destination (special cases with
    chained pickings)

    * /set_destination_package
    * /set_destination_line

    """

    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()
        # Test split of partial qty when the moves have "move_orig_ids".
        # We create a chain of pickings to ensure the proper state is computed
        # for the split move.
        cls.picking_a = picking_a = cls._create_picking(lines=[(cls.product_c, 10)])
        cls.picking_b = picking_b = cls._create_picking(lines=[(cls.product_c, 10)])
        # connect a and b in a chain of moves
        for move_a in picking_a.move_lines:
            for move_b in picking_b.move_lines:
                if move_a.product_id == move_b.product_id:
                    move_a.move_dest_ids = move_b
                    move_b.procure_method = "make_to_order"

        cls.pickings = picking_a | picking_b
        cls._fill_stock_for_moves(picking_a.move_lines, location=cls.content_loc)
        cls.pickings.action_assign()

        cls.dest_location = (
            cls.env["stock.location"]
            .sudo()
            .create(
                {
                    "name": "Sub Shelf 1",
                    "barcode": "subshelf1",
                    "location_id": cls.shelf1.id,
                }
            )
        )

    def test_set_destination_line_partial_qty_with_move_orig_ids(self):
        """Scanned destination location with partial qty, but related moves
        has to be split and the move has origin moves (with origin moves)
        """
        picking_a = self.picking_a
        picking_b = self.picking_b
        picking_a.move_line_ids.qty_done = 10
        picking_a.action_done()
        self.assertEqual(picking_a.state, "done")
        self.assertEqual(picking_b.state, "assigned")
        self._simulate_pickings_selected(picking_b)

        move_line_c = picking_b.move_line_ids.filtered(
            lambda m: m.product_id == self.product_c
        )
        move = move_line_c.move_id

        self.assertEqual(move_line_c.product_uom_qty, 10)
        self.assertEqual(move_line_c.qty_done, 10)
        # Scan partial qty (6/10)
        self.service.dispatch(
            "set_destination_line",
            params={
                "location_id": self.content_loc.id,
                "move_line_id": move_line_c.id,
                "quantity": move_line_c.product_uom_qty - 4,  # Scan 6 qty
                "barcode": self.dest_location.barcode,
            },
        )
        done_picking = move_line_c.picking_id
        # Check move line data
        self.assertEqual(picking_b.backorder_ids, done_picking)
        self.assertEqual(move_line_c.move_id.product_uom_qty, 6)
        self.assertEqual(move_line_c.product_uom_qty, 0)
        self.assertEqual(move_line_c.qty_done, 6)
        self.assertEqual(move_line_c.state, "done")
        # the move has been split
        self.assertNotEqual(move_line_c.move_id, move)

        # Check the move handling the remaining qty
        self.assertEqual(move.state, "assigned")
        move_line = move.move_line_ids
        self.assertEqual(move_line.move_id.product_uom_qty, 4)
        self.assertEqual(move_line.product_uom_qty, 4)
        self.assertEqual(move_line.qty_done, 4)

    def test_set_destination_package_partial_qty_with_move_orig_ids(self):
        """Scanned destination location with partial qty, but related moves
        has to be split and the move has origin moves
        (with package and origin moves)
        """
        picking_a = self.picking_a
        picking_b = self.picking_b

        # we put 6 in a new package and 4 in another new package
        package1 = self.env["stock.quant.package"].create({})
        package2 = self.env["stock.quant.package"].create({})
        line1 = picking_a.move_line_ids
        line2 = line1.copy({"product_uom_qty": 4, "qty_done": 4})
        line1.with_context(bypass_reservation_update=True).product_uom_qty = 6
        line1.qty_done = 6
        line1.result_package_id = package1
        line2.result_package_id = package2
        picking_a.action_done()
        self.assertEqual(picking_a.state, "done")
        self.assertEqual(picking_b.state, "assigned")
        # we have 1 move line per package
        self.assertEqual(len(picking_b.move_line_ids), 2)
        self._simulate_pickings_selected(picking_b)

        move_line = picking_b.move_line_ids.filtered(lambda m: m.package_id == package1)
        move = move_line.move_id

        self.assertEqual(move_line.product_uom_qty, 6.0)
        self.assertEqual(move_line.qty_done, 6.0)
        # Scan partial qty (6/10)
        self.service.dispatch(
            "set_destination_line",
            params={
                "location_id": self.content_loc.id,
                "move_line_id": move_line.id,
                "quantity": 6.0,  # Scan 6 qty
                "barcode": self.dest_location.barcode,
            },
        )
        # Check move line data
        self.assertEqual(move_line.move_id.product_uom_qty, 6)
        self.assertEqual(move_line.product_uom_qty, 0)
        self.assertEqual(move_line.qty_done, 6)
        self.assertEqual(move_line.state, "done")

        # Check the move handling the remaining qty
        remaining_move = picking_b.move_lines - move
        self.assertEqual(remaining_move.state, "assigned")
        remaining_move_line = remaining_move.move_line_ids
        self.assertEqual(remaining_move_line.move_id.product_uom_qty, 4)
        self.assertEqual(remaining_move_line.product_uom_qty, 4)
        self.assertEqual(remaining_move_line.qty_done, 4)
