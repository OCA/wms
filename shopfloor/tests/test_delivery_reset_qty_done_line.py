# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from .test_delivery_base import DeliveryCommonCase

# pylint: disable=missing-return


class DeliveryResetQtyDoneLineCase(DeliveryCommonCase):
    """Tests for /reset_qty_done_line"""

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
        cls.pack1_moves = picking.move_ids[:2]
        cls.raw_move = picking.move_ids[2]
        cls._fill_stock_for_moves(cls.pack1_moves, in_package=True)
        cls._fill_stock_for_moves(cls.raw_move)
        picking.action_assign()
        # Some records not related at all to the processed picking
        cls.free_picking = cls._create_picking(lines=[(cls.product_d, 10)])
        cls.free_raw_move = cls.free_picking.move_ids[0]
        cls._fill_stock_for_moves(cls.free_raw_move)
        cls.free_picking.action_assign()

    def test_reset_qty_done_line_picking_not_found(self):
        move_lines = self.pack1_moves.mapped("move_line_ids")
        response = self.service.dispatch(
            "reset_qty_done_line",
            params={"move_line_id": move_lines[0].id, "picking_id": -1},
        )
        self.assert_response_deliver(
            response, message=self.service.msg_store.stock_picking_not_found()
        )

    def test_reset_qty_done_line_line_not_found(self):
        response = self.service.dispatch(
            "reset_qty_done_line",
            params={"move_line_id": -1, "picking_id": self.picking.id},
        )
        self.assert_response_deliver(
            response,
            picking=self.picking,
            message=self.service.msg_store.record_not_found(),
        )

    def test_reset_qty_done_line_line_not_available_in_picking(self):
        move_line = self.free_raw_move.mapped("move_line_ids")
        response = self.service.dispatch(
            "reset_qty_done_line",
            params={"move_line_id": move_line.id, "picking_id": self.picking.id},
        )
        self.assert_response_deliver(
            response,
            picking=self.picking,
            message=self.service.msg_store.line_not_available_in_picking(self.picking),
        )

    def test_reset_qty_done_line_ok(self):
        move_line = self.raw_move.mapped("move_line_ids")
        # Set qty done on a line
        self.service.dispatch(
            "set_qty_done_line",
            params={"move_line_id": move_line.id, "picking_id": self.picking.id},
        )
        self.assertTrue(move_line.qty_done == move_line.reserved_uom_qty)
        # Reset it, no related move lines are "done"
        response = self.service.dispatch(
            "reset_qty_done_line",
            params={"move_line_id": move_line.id, "picking_id": self.picking.id},
        )
        self.assert_response_deliver(response, picking=self.picking)
        self.assertFalse(move_line.qty_done)

    def test_reset_qty_done_line_with_package(self):
        move_line = self.pack1_moves[0].mapped("move_line_ids")
        response = self.service.dispatch(
            "set_qty_done_line",
            params={"move_line_id": move_line.id, "picking_id": self.picking.id},
        )
        self.assert_response_deliver(
            response,
            picking=self.picking,
            message=self.service.msg_store.line_has_package_scan_package(),
        )

    def test_reset_qty_done_pack_picking_status(self):
        move_lines = self.picking.move_line_ids
        raw_move_line = self.raw_move.mapped("move_line_ids")
        # Set qty done for all lines (some are linked to packages here),
        # picking is automatically set to done
        for package in move_lines.mapped("package_id"):
            self.service.dispatch(
                "set_qty_done_pack",
                params={"package_id": package.id, "picking_id": self.picking.id},
            )
        self.service.dispatch(
            "set_qty_done_line",
            params={"move_line_id": raw_move_line.id, "picking_id": self.picking.id},
        )
        self.assertEqual(self.picking.state, "done")
        # Try to reset one of them => picking already processed
        response = self.service.dispatch(
            "reset_qty_done_line",
            params={"move_line_id": raw_move_line.id, "picking_id": self.picking.id},
        )
        self.assert_response_deliver(
            response, message=self.service.msg_store.already_done()
        )
        self.assertEqual(self.picking.state, "done")
