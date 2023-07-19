# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from .test_delivery_base import DeliveryCommonCase

# pylint: disable=missing-return


class DeliverySetQtyDoneLineCase(DeliveryCommonCase):
    """Tests for /set_qty_done_line"""

    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()
        cls.picking = picking = cls._create_picking(
            lines=[
                # put A in a package
                (cls.product_a, 10),
                # B as raw product
                (cls.product_b, 10),
            ]
        )
        cls.pack1_move = picking.move_ids[0]
        cls.raw_move = picking.move_ids[1]
        cls._fill_stock_for_moves(cls.pack1_move, in_package=True)
        cls._fill_stock_for_moves(cls.raw_move)
        picking.action_assign()

    def _test_set_qty_done_line_ok(self, move_line):
        response = self.service.dispatch(
            "set_qty_done_line",
            params={"move_line_id": move_line.id, "picking_id": self.picking.id},
        )
        self.assert_qty_done(move_line)
        self.assert_response_deliver(response, picking=self.picking)

    def test_set_qty_done_line_picking_not_found(self):
        move_line = self.pack1_move.mapped("move_line_ids")
        response = self.service.dispatch(
            "set_qty_done_line", params={"move_line_id": move_line.id, "picking_id": -1}
        )
        self.assert_response_deliver(
            response, message=self.service.msg_store.stock_picking_not_found()
        )

    def test_set_qty_done_line_picking_canceled(self):
        move_line = self.pack1_move.mapped("move_line_ids")
        self.picking.action_cancel()
        response = self.service.dispatch(
            "set_qty_done_line",
            params={"move_line_id": move_line.id, "picking_id": self.picking.id},
        )
        self.assert_response_deliver(
            response,
            message=self.service.msg_store.stock_picking_not_available(self.picking),
        )

    def test_set_qty_done_line_line_not_found(self):
        response = self.service.dispatch(
            "set_qty_done_line",
            params={"move_line_id": -1, "picking_id": self.picking.id},
        )
        self.assert_response_deliver(
            response,
            picking=self.picking,
            message=self.service.msg_store.record_not_found(),
        )

    def test_set_qty_done_line_ok(self):
        move_line = self.raw_move.mapped("move_line_ids")
        self._test_set_qty_done_line_ok(move_line)
        # picking is still assigned as only one move line have been processed
        self.assertEqual(self.picking.state, "assigned")

    def test_set_qty_done_line_picking_done(self):
        # process the first move line with a package
        move_line = self.pack1_move.mapped("move_line_ids")
        package = move_line.mapped("package_id")
        self.service.dispatch(
            "set_qty_done_pack",
            params={"package_id": package.id, "picking_id": self.picking.id},
        )
        self.assertEqual(self.picking.state, "assigned")
        # process the remaining move line
        move_line = self.raw_move.mapped("move_line_ids")
        self.service.dispatch(
            "set_qty_done_line",
            params={"move_line_id": move_line.id, "picking_id": self.picking.id},
        )
        # picking is done once all its moves have been processed
        self.assertEqual(self.picking.state, "done")
