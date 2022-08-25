# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from .common import CommonCase


class TestSetDestination(CommonCase):
    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()
        cls.packing_location.sudo().active = True
        cls.location_dest = cls.env.ref("stock.stock_location_stock")

    @classmethod
    def _change_line_dest(cls, line):
        # Modify the location dest on the move, so we have different children
        # for move's dest_location and pick type's dest_location
        line.location_dest_id = cls.location_dest

    def test_scan_location_child_of_dest_location(self):
        picking = self._create_picking()
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        self._change_line_dest(selected_move_line)
        response = self.service.dispatch(
            "set_destination",
            params={
                "picking_id": picking.id,
                "selected_line_ids": selected_move_line.ids,
                "location_id": self.shelf2.id,
            },
        )
        self.assertEqual(selected_move_line.location_dest_id, self.shelf2)
        data = self.data.picking(picking)
        data.update({"move_lines": self.data.move_lines(picking.move_line_ids)})
        self.assert_response(
            response,
            next_state="select_line",
            data={"picking": data},
        )

    def test_scan_location_child_of_pick_type_dest_location(self):
        picking = self._create_picking()
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        self._change_line_dest(selected_move_line)
        response = self.service.dispatch(
            "set_destination",
            params={
                "picking_id": picking.id,
                "selected_line_ids": selected_move_line.ids,
                "location_id": self.dispatch_location.id,
            },
        )
        # location is a child of the picking type's location. destination location
        # hasn't been set
        self.assertNotEqual(selected_move_line.location_dest_id, self.dispatch_location)
        # But a confirmation has been asked
        data = self.data.picking(picking)
        self.assert_response(
            response,
            next_state="set_destination",
            data={
                "picking": data,
                "selected_move_lines": self.data.move_lines(selected_move_line),
            },
            message={
                "message_type": "warning",
                "body": f"Place it in {self.dispatch_location.name}?",
            },
        )
        # Send the same message with confirmation=True to confirm
        response = self.service.dispatch(
            "set_destination",
            params={
                "picking_id": picking.id,
                "selected_line_ids": selected_move_line.ids,
                "location_id": self.dispatch_location.id,
                "confirmation": True,
            },
        )
        self.assertEqual(selected_move_line.location_dest_id, self.dispatch_location)
        data = self.data.picking(picking)
        data.update({"move_lines": self.data.move_lines(picking.move_line_ids)})
        self.assert_response(
            response,
            next_state="select_line",
            data={"picking": data},
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
                "selected_line_ids": selected_move_line.ids,
                "location_id": self.shelf1.id,
            },
        )
        data = self.data.picking(picking)
        self.assert_response(
            response,
            next_state="set_destination",
            data={
                "picking": data,
                "selected_move_lines": self.data.move_lines(selected_move_line),
            },
            message={"message_type": "error", "body": "You cannot place it here."},
        )
