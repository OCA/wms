# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from .test_delivery_base import DeliveryCommonCase

# pylint: disable=missing-return


class DeliverySetQtyDonePackCase(DeliveryCommonCase):
    """Tests for /set_qty_done_pack"""

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
                # D in two different packages
                (cls.product_d, 10),
            ]
        )
        cls.pack1_moves = picking.move_ids[:2]
        cls.pack2_move = picking.move_ids[2]
        cls.pack3_move = picking.move_ids[3]
        cls._fill_stock_for_moves(cls.pack1_moves, in_package=True)
        cls._fill_stock_for_moves(cls.pack2_move, in_package=True)
        # Fill stock for D moves (two packages)
        for __ in range(2):
            product_d_pkg = cls.env["stock.quant.package"].create({})
            cls._update_qty_in_location(
                cls.pack3_move.location_id,
                cls.pack3_move.product_id,
                5,
                package=product_d_pkg,
            )
        picking.action_assign()

    def _test_set_qty_done_pack_ok(self, move_lines, package, qties=None):
        response = self.service.dispatch(
            "set_qty_done_pack",
            params={"package_id": package.id, "picking_id": self.picking.id},
        )
        self.assert_qty_done(move_lines, qties=qties)
        self.assert_response_deliver(response, picking=self.picking)

    def test_set_qty_done_pack_picking_not_found(self):
        move_lines = self.pack1_moves.mapped("move_line_ids")
        package = move_lines.mapped("package_id")
        response = self.service.dispatch(
            "set_qty_done_pack", params={"package_id": package.id, "picking_id": -1}
        )
        self.assert_response_deliver(
            response, message=self.service.msg_store.stock_picking_not_found()
        )

    def test_set_qty_done_pack_picking_canceled(self):
        move_lines = self.pack1_moves.mapped("move_line_ids")
        package = move_lines.mapped("package_id")
        self.picking.action_cancel()
        response = self.service.dispatch(
            "set_qty_done_pack",
            params={"package_id": package.id, "picking_id": self.picking.id},
        )
        self.assert_response_deliver(
            response,
            message=self.service.msg_store.stock_picking_not_available(self.picking),
        )

    def test_set_qty_done_pack_package_not_found(self):
        response = self.service.dispatch(
            "set_qty_done_pack",
            params={"package_id": -1, "picking_id": self.picking.id},
        )
        self.assert_response_deliver(
            response,
            picking=self.picking,
            message=self.service.msg_store.package_not_found(),
        )

    def test_set_qty_done_pack_multiple_product_ok(self):
        move_lines = self.pack1_moves.mapped("move_line_ids")
        package = move_lines.mapped("package_id")
        self._test_set_qty_done_pack_ok(move_lines, package)

    def test_set_qty_done_pack_one_product_ok(self):
        move_lines = self.pack2_move.mapped("move_line_ids")
        package = move_lines.mapped("package_id")
        self._test_set_qty_done_pack_ok(move_lines, package)

    def test_set_qty_done_pack_product_in_multiple_packages_ok(self):
        move_lines = self.pack3_move.mapped("move_line_ids")
        first_package = move_lines.mapped("package_id")[0]
        self._test_set_qty_done_pack_ok(
            move_lines,
            # first_package done, not the second
            first_package,
            qties=[5, 0],
        )

    def test_set_qty_done_pack_picking_done(self):
        pack1_move_lines = self.pack1_moves.mapped("move_line_ids")
        package1 = pack1_move_lines.mapped("package_id")
        pack2_move_lines = self.pack2_move.mapped("move_line_ids")
        package2 = pack2_move_lines.mapped("package_id")
        pack3_move_lines = self.pack3_move.mapped("move_line_ids")
        packages3 = pack3_move_lines.mapped("package_id")
        # process first package
        self.service.dispatch(
            "set_qty_done_pack",
            params={"package_id": package1.id, "picking_id": self.picking.id},
        )
        self.assertEqual(self.picking.state, "assigned")
        # process second package
        self.service.dispatch(
            "set_qty_done_pack",
            params={"package_id": package2.id, "picking_id": self.picking.id},
        )
        self.assertEqual(self.picking.state, "assigned")
        # process third package
        self.service.dispatch(
            "set_qty_done_pack",
            params={"package_id": packages3[0].id, "picking_id": self.picking.id},
        )
        self.assertEqual(self.picking.state, "assigned")
        # process last package
        self.service.dispatch(
            "set_qty_done_pack",
            params={"package_id": packages3[1].id, "picking_id": self.picking.id},
        )
        # picking is done once all its moves have been processed
        self.assertEqual(self.picking.state, "done")
