# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from .common import CommonCase


class TestSetDestination(CommonCase):
    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()
        cls.packing_location.sudo().active = True
        cls.parent_location_dest = cls.env.ref("stock.stock_location_stock")
        cls.location_dest = cls.shelf2
        cls.another_location = cls.env["stock.location"].search(
            [("parent_path", "not ilike", cls.parent_location_dest.parent_path)],
            limit=1,
        )

    @classmethod
    def _change_line_dest(cls, line):
        # Modify the location dest on the move, so we have different children
        # for move's dest_location and pick type's dest_location
        line.location_dest_id = cls.location_dest

    def test_scan_location_child_of_dest_location(self):
        picking = self._create_picking()
        picking.sudo().picking_type_id.default_location_dest_id = self.another_location
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        self._change_line_dest(selected_move_line)
        response = self.service.dispatch(
            "set_destination",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "location_name": self.parent_location_dest.name,
            },
        )
        self.assertEqual(selected_move_line.location_dest_id, self.parent_location_dest)
        self.assert_response(
            response,
            next_state="select_move",
            data=self._data_for_select_move(picking),
        )

    def test_scan_location_child_of_pick_type_dest_location(self):
        picking = self._create_picking()
        picking.sudo().picking_type_id.default_location_dest_id = self.shelf2
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        selected_move_line.location_dest_id = self.another_location
        response = self.service.dispatch(
            "set_destination",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "location_name": self.parent_location_dest.name,
            },
        )
        # location is a child of the picking type's location. destination location
        # hasn't been set
        self.assertNotEqual(
            selected_move_line.location_dest_id, self.parent_location_dest
        )
        # But a confirmation has been asked
        data = self.data.picking(picking)
        self.assert_response(
            response,
            next_state="set_destination",
            data={
                "picking": data,
                "selected_move_line": self.data.move_lines(selected_move_line),
            },
            message={
                "message_type": "warning",
                "body": f"Place it in {self.parent_location_dest.name}?",
            },
        )
        # Send the same message with confirmation=True to confirm
        response = self.service.dispatch(
            "set_destination",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "location_name": self.parent_location_dest.name,
                "confirmation": True,
            },
        )
        self.assertEqual(selected_move_line.location_dest_id, self.parent_location_dest)
        self.assert_response(
            response,
            next_state="select_move",
            data=self._data_for_select_move(picking),
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
            },
            message={"message_type": "error", "body": "You cannot place it here"},
        )

    def test_auto_posting(self):
        self.menu.sudo().auto_post_line = True
        picking = self._create_picking()
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        self._change_line_dest(selected_move_line)

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
        self.service.dispatch(
            "set_destination",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "location_name": self.parent_location_dest.name,
            },
        )
        # The line has been moved to a different picking.
        self.assertNotEqual(picking, selected_move_line.picking_id)
        # Its qty_done is 3.
        self.assertEqual(selected_move_line.qty_done, 3)
        # The new picking is marked as done.
        self.assertEqual(selected_move_line.picking_id.state, "done")

        # The line that remained in the original picking
        # for that product has a product_uom_qty of 7
        # and a qty_done of 0.
        line_in_picking = picking.move_line_ids.filtered(
            lambda l: l.product_id == selected_move_line.product_id
        )
        self.assertEqual(line_in_picking.product_uom_qty, 7)
        self.assertEqual(line_in_picking.qty_done, 0)
        self.assertEqual(picking.state, "assigned")
