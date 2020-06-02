# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from .test_delivery_base import DeliveryCommonCase


class DeliveryResetQtyDonePackCase(DeliveryCommonCase):
    """Tests for /reset_qty_done_pack"""

    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()
        cls.picking = picking = cls._create_picking(
            lines=[
                # we'll put A and B in a single package
                (cls.product_a, 10),
                (cls.product_b, 10),
                # C alone in a package
                (cls.product_c, 10),
            ]
        )
        cls.pack1_moves = picking.move_lines[:2]
        cls.pack2_move = picking.move_lines[2]
        cls._fill_stock_for_moves(cls.pack1_moves, in_package=True)
        cls._fill_stock_for_moves(cls.pack2_move, in_package=True)
        picking.action_assign()
        # Some records not related at all to the processed picking
        cls.free_package = cls.env["stock.quant.package"].create(
            {"name": "FREE_PACKAGE"}
        )

    def test_reset_qty_done_pack_picking_not_found(self):
        move_lines = self.pack1_moves.mapped("move_line_ids")
        package = move_lines.mapped("package_id")
        response = self.service.dispatch(
            "reset_qty_done_pack", params={"package_id": package.id, "picking_id": -1}
        )
        self.assert_response_deliver(
            response, message=self.service.msg_store.stock_picking_not_found()
        )

    def test_reset_qty_done_pack_package_not_found(self):
        response = self.service.dispatch(
            "reset_qty_done_pack",
            params={"package_id": -1, "picking_id": self.picking.id},
        )
        self.assert_response_deliver(
            response,
            picking=self.picking,
            message=self.service.msg_store.package_not_found(),
        )

    def test_reset_qty_done_pack_package_not_available_in_picking(self):
        response = self.service.dispatch(
            "reset_qty_done_pack",
            params={"package_id": self.free_package.id, "picking_id": self.picking.id},
        )
        self.assert_response_deliver(
            response,
            picking=self.picking,
            message=self.service.msg_store.package_not_available_in_picking(
                self.free_package, self.picking
            ),
        )

    def test_reset_qty_done_pack_ok(self):
        move_lines = self.pack1_moves.mapped("move_line_ids")
        package = move_lines.mapped("package_id")
        # Set qty done on a package, related move lines are "done"
        self.service.dispatch(
            "set_qty_done_pack",
            params={"package_id": package.id, "picking_id": self.picking.id},
        )
        self.assertTrue(all(ml.qty_done == ml.product_uom_qty for ml in move_lines))
        # Reset it, no related move lines are "done"
        response = self.service.dispatch(
            "reset_qty_done_pack",
            params={"package_id": package.id, "picking_id": self.picking.id},
        )
        self.assert_response_deliver(response, picking=self.picking)
        self.assertFalse(any(ml.qty_done > 0 for ml in move_lines))

    def test_reset_qty_done_pack_picking_status(self):
        package1 = self.pack1_moves.mapped("move_line_ids").mapped("package_id")
        package2 = self.pack2_move.mapped("move_line_ids").mapped("package_id")
        # Set qty done for all lines (all linked to packages here), picking is
        # automatically set to done
        self.service.dispatch(
            "set_qty_done_pack",
            params={"package_id": package1.id, "picking_id": self.picking.id},
        )
        self.service.dispatch(
            "set_qty_done_pack",
            params={"package_id": package2.id, "picking_id": self.picking.id},
        )
        self.assertEqual(self.picking.state, "done")
        # Try to reset one of them => picking already processed
        response = self.service.dispatch(
            "reset_qty_done_pack",
            params={"package_id": package1.id, "picking_id": self.picking.id},
        )
        self.assert_response_deliver(
            response, message=self.service.msg_store.already_done()
        )
        self.assertEqual(self.picking.state, "done")
