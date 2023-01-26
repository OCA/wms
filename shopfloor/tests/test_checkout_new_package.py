# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from .test_checkout_base import CheckoutCommonCase
from .test_checkout_select_package_base import CheckoutSelectPackageMixin


class CheckoutNewPackageCase(CheckoutCommonCase, CheckoutSelectPackageMixin):
    def test_new_package_ok(self):
        picking = self._create_picking(
            lines=[
                (self.product_a, 10),
                (self.product_b, 10),
                (self.product_c, 10),
                (self.product_d, 10),
            ]
        )
        pack1_moves = picking.move_lines[:3]
        pack2_moves = picking.move_lines[3:]
        # put in 2 packs, for this test, we'll work on pack1
        self._fill_stock_for_moves(pack1_moves, in_package=True)
        self._fill_stock_for_moves(pack2_moves, in_package=True)
        picking.action_assign()

        selected_lines = pack1_moves.move_line_ids
        pack1 = pack1_moves.move_line_ids.package_id

        move_line1, move_line2, move_line3 = selected_lines
        # we'll put only the first 2 lines (product A and B) in the new package
        move_line1.qty_done = move_line1.product_uom_qty
        move_line2.qty_done = move_line2.product_uom_qty
        move_line3.qty_done = 0

        response = self.service.dispatch(
            "new_package",
            params={"picking_id": picking.id, "selected_line_ids": selected_lines.ids},
        )

        new_package = move_line1.result_package_id
        self.assertNotEqual(pack1, new_package)

        self.assertRecordValues(
            move_line1,
            [{"result_package_id": new_package.id, "shopfloor_checkout_done": True}],
        )
        self.assertRecordValues(
            move_line2,
            [{"result_package_id": new_package.id, "shopfloor_checkout_done": True}],
        )
        self.assertRecordValues(
            move_line3,
            # qty_done was zero so we don't set it as packed and it remains in
            # the same package
            [{"result_package_id": pack1.id, "shopfloor_checkout_done": False}],
        )
        self.assert_response(
            response,
            # go pack to the screen to select lines to put in packages
            next_state="select_line",
            data=self._data_for_select_line(picking),
            message=self.msg_store.goods_packed_in(new_package),
        )
