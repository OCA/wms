# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from .test_delivery_base import DeliveryCommonCase


class DeliveryDoneCase(DeliveryCommonCase):
    """Tests for /done"""

    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()
        cls.picking = picking = cls._create_picking(
            lines=[
                # we'll put A and B in a single package
                (cls.product_a, 10),
                (cls.product_b, 10),
                # C as raw product
                (cls.product_c, 10),
            ]
        )
        cls.pack1_moves = picking.move_lines[:2]
        cls.raw_move = cls.picking.move_lines[2]
        cls._fill_stock_for_moves(cls.pack1_moves, in_package=True)
        cls._fill_stock_for_moves(cls.raw_move)
        cls.picking.action_assign()

    def assert_response_confirm_done(self, response, picking=None, message=None):
        self.assert_response(
            response,
            next_state="confirm_done",
            data={"picking": self._stock_picking_data(picking) if picking else None},
            message=message,
        )

    def test_done_picking_not_found(self):
        response = self.service.dispatch("done", params={"picking_id": -1})
        self.assert_response_deliver(
            response, message=self.service.msg_store.stock_picking_not_found()
        )

    def test_done_all_qty_done(self):
        # Do not use the /set_qty_done_line endpoint to set done qties to not
        # update the picking to 'done' state automatically
        for move_line in self.picking.move_line_ids:
            move_line.qty_done = move_line.product_uom_qty
        response = self.service.dispatch("done", params={"picking_id": self.picking.id})
        self.assert_response_deliver(
            response,
            message=self.service.msg_store.transfer_complete(self.picking),
        )
        self.assertEqual(self.picking.state, "done")

    def test_done_no_qty_done(self):
        response = self.service.dispatch("done", params={"picking_id": self.picking.id})
        self.assert_response_confirm_done(
            response,
            picking=self.picking,
            message=self.service.msg_store.transfer_confirm_done(),
        )
        self.assertEqual(self.picking.state, "assigned")

    def test_done_some_qty_done(self):
        move_line = self.raw_move.move_line_ids[0]
        self.service.dispatch(
            "set_qty_done_line",
            params={"move_line_id": move_line.id, "picking_id": self.picking.id},
        )
        response = self.service.dispatch("done", params={"picking_id": self.picking.id})
        self.assert_response_confirm_done(
            response,
            picking=self.picking,
            message=self.service.msg_store.transfer_confirm_done(),
        )
        self.assertEqual(self.picking.state, "assigned")

    def test_done_no_qty_done_confirm(self):
        self.assertEqual(self.picking.state, "assigned")
        response = self.service.dispatch(
            "done", params={"picking_id": self.picking.id, "confirm": True}
        )
        self.assert_response_deliver(
            response,
            message=self.service.msg_store.transfer_no_qty_done(),
        )
        self.assertEqual(self.picking.state, "assigned")

    def test_done_some_qty_done_confirm(self):
        move_line = self.raw_move.move_line_ids[0]
        self.service.dispatch(
            "set_qty_done_line",
            params={"move_line_id": move_line.id, "picking_id": self.picking.id},
        )
        self.assertEqual(self.picking.state, "assigned")
        response = self.service.dispatch(
            "done", params={"picking_id": self.picking.id, "confirm": True}
        )
        self.assert_response_deliver(
            response,
            message=self.service.msg_store.transfer_complete(self.picking),
        )
        self.assertEqual(self.picking.state, "done")
        self.assertEqual(self.picking.move_lines, self.raw_move)
        backorder = self.picking.backorder_ids
        self.assertTrue(backorder)
        self.assertEqual(self.pack1_moves.picking_id, backorder)
