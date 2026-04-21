# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
# pylint: disable=missing-return
from .common import CommonCase


class TestSetDestination(CommonCase):
    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()
        cls.packing_location.sudo().active = True
        cls.sub_input_location = (
            cls.env["stock.location"]
            .sudo()
            .create(
                {
                    "name": "Test Reception Shelf",
                    "location_id": cls.input_location.id,
                }
            )
        )
        cls.sub_input_location_2 = (
            cls.env["stock.location"]
            .sudo()
            .create(
                {
                    "name": "Test Reception Shelf 2",
                    "location_id": cls.input_location.id,
                }
            )
        )
        cls.sub_stock_location = (
            cls.env["stock.location"]
            .sudo()
            .create(
                {
                    "name": "Test Reception Shelf",
                    "location_id": cls.stock_location.id,
                }
            )
        )

    def test_scan_location_child_of_dest_location(self):
        picking = self._create_picking()
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        self.assertTrue(
            self.sub_input_location.is_sublocation_of(picking.location_dest_id)
        )
        self.assertNotEqual(
            self.sub_input_location, selected_move_line.location_dest_id
        )

        response = self.service.dispatch(
            "set_destination",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "location_name": self.sub_input_location.name,
            },
        )
        self.assertEqual(selected_move_line.location_dest_id, self.sub_input_location)
        self.assert_response(
            response, next_state="select_move", data=self._data_for_select_move(picking)
        )

    def test_scan_location_valid_but_unexpected(self):
        picking = self._create_picking()
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )

        selected_move_line.location_dest_id = self.sub_input_location
        # `sub_input_location_2` is valid but not the expected location
        response = self.service.dispatch(
            "set_destination",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "location_name": self.sub_input_location_2.name,
            },
        )
        self.assertMessage(
            response,
            self.msg_store.place_in_location_ask_confirmation(
                self.sub_input_location_2.name
            ),
        )
        self.assertNotEqual(
            selected_move_line.location_dest_id, self.sub_input_location_2
        )

        response = self.service.dispatch(
            "set_destination",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "location_name": self.sub_input_location_2.name,
                "confirmation": self.sub_input_location_2.name,
            },
        )
        self.assertEqual(selected_move_line.location_dest_id, self.sub_input_location_2)
        self.assert_response(
            response, next_state="select_move", data=self._data_for_select_move(picking)
        )

    def test_scan_location_not_child_of_dest_locations(self):
        picking = self._create_picking()
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        response = self.service.dispatch(
            "set_destination",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "location_name": self.shelf1.name,
            },
        )
        data = self.data.picking(picking)
        self.assert_response(
            response,
            next_state="set_destination",
            data={
                "picking": data,
                "selected_move_line": self.data.move_lines(selected_move_line),
                "confirmation": None,
            },
            message={"message_type": "error", "body": "You cannot place it here"},
        )

    def test_auto_posting_partial(self):
        self.menu.sudo().auto_post_line = True
        # Creating a picking with a single move, with qty todo = 10
        picking = self._create_picking(lines=[(self.product_a, 10)])
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )

        # User has previously scanned a total of 3 units (with 7 still to do).
        # A new pack has been created and assigned to the line.
        self.service.dispatch(
            "process_with_new_pack",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "quantity": 3,
            },
        )

        # If the auto_post_line option is checked,
        # and dest package & dest location are set,
        # a line with 3 demand will be automatically extracted
        # in a new picking, which will be marked as done.
        response = self.service.dispatch(
            "set_destination",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "location_name": self.dispatch_location.name,
            },
        )
        # Next screen is select move, because picking is not done
        self.assert_response(
            response, next_state="select_move", data=self._data_for_select_move(picking)
        )
        # The line has been moved to a different picking.
        self.assertNotEqual(picking, selected_move_line.picking_id)
        # Its qty_done is 3.
        self.assertEqual(selected_move_line.qty_done, 3)
        # The new picking is marked as done.
        self.assertEqual(selected_move_line.picking_id.state, "done")

        # The line that remained in the original picking
        line_in_picking = picking.move_line_ids.filtered(
            lambda l: l.product_id == selected_move_line.product_id
        )
        self.assertEqual(line_in_picking.reserved_uom_qty, 7)
        self.assertEqual(line_in_picking.qty_done, 0)
        self.assertEqual(picking.state, "assigned")

    def test_auto_posting_full_one_line(self):
        self.menu.sudo().auto_post_line = True
        # Create a picking with a single move with qty todo = 10
        picking = self._create_picking(lines=[(self.product_a, 10)])
        selected_move_line = picking.move_line_ids.filtered(
            lambda li: li.product_id == self.product_a
        )
        # User has previously scanned the full qty
        # A new pack has been created and assigned to the line.
        self.service.dispatch(
            "process_with_new_pack",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "quantity": 10,
            },
        )
        # Full qty processed, picking is done, and next screen is select document.
        response = self.service.dispatch(
            "set_destination",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "location_name": self.dispatch_location.name,
            },
        )
        message = self.msg_store.transfer_done_success(picking)
        self.assert_response(
            response, next_state="select_document", data=self.ANY, message=message
        )

    def test_auto_posting_full_two_lines(self):
        self.menu.sudo().auto_post_line = True
        # Create a picking with a two moves with qty todo = 10
        picking = self._create_picking()
        selected_move_line = picking.move_line_ids.filtered(
            lambda li: li.product_id == self.product_a
        )
        # User has previously scanned the full qty
        # A new pack has been created and assigned to the line.
        self.service.dispatch(
            "process_with_new_pack",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "quantity": 10,
            },
        )
        # Full qty processed, but one more line to process,
        # next screen is select_move
        response = self.service.dispatch(
            "set_destination",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "location_name": self.dispatch_location.name,
            },
        )
        self.assert_response(
            response, next_state="select_move", data=self._data_for_select_move(picking)
        )
        # Lines has been moved in another picking
        self.assertNotEqual(picking, selected_move_line.picking_id)
        # Fully processed
        self.assertEqual(selected_move_line.picking_id.state, "done")
        # One move remaining in the picking, for product b, still to be processed
        self.assertEqual(picking.move_ids.product_id, self.product_b)

    def test_auto_posting_concurrent_work(self):
        """Check 2 users working on the same move.

        With the auto post line option On.

        """
        self.menu.sudo().auto_post_line = True
        picking = self._create_picking(lines=[(self.product_a, 10)])
        move = picking.move_ids
        # User 1 starts working
        service_u1 = self.service
        res_u1 = service_u1.dispatch(
            "manual_select_move",
            params={"move_id": move.id},
        )
        # User 2 starts working on the same move
        service_u2 = self._get_service_for_user(self.shopfloor_manager)
        service_u2.dispatch(
            "manual_select_move",
            params={"move_id": move.id},
        )
        self.assertEqual(len(move.move_line_ids), 2)
        # User 1 finishes his work
        move_line_data = res_u1["data"]["set_quantity"]["selected_move_line"][0]
        line_id_u1 = move_line_data["id"]
        res_u1 = service_u1.dispatch(
            "process_without_pack",
            params={
                "picking_id": picking.id,
                "selected_line_id": line_id_u1,
                "quantity": 1,
            },
        )
        res_u1 = service_u1.dispatch(
            "set_destination",
            params={
                "picking_id": picking.id,
                "selected_line_id": line_id_u1,
                "location_name": self.dispatch_location.name,
            },
        )
        # With the auto post line option
        # The work done is moved and done in a specific transfer
        self.assertEqual(picking.state, "assigned")
        # So the quantity left to do on the current move has decreased
        self.assertEqual(move.product_uom_qty, 9)
