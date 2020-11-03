# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from .test_checkout_base import CheckoutCommonCase
from .test_checkout_select_package_base import CheckoutSelectPackageMixin


class CheckoutNoPackageCase(CheckoutCommonCase, CheckoutSelectPackageMixin):
    def test_no_package_ok(self):
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
        self._fill_stock_for_moves(pack1_moves)
        self._fill_stock_for_moves(pack2_moves)
        picking.action_assign()

        move_line1, move_line2, move_line3 = pack1_moves.move_line_ids
        selected_lines = move_line1 + move_line2

        # we'll put only the first 2 lines (product A and B) w/ no package
        move_line1.qty_done = move_line1.product_uom_qty
        move_line2.qty_done = move_line2.product_uom_qty
        move_line3.qty_done = 0

        response = self.service.dispatch(
            "no_package",
            params={"picking_id": picking.id, "selected_line_ids": selected_lines.ids},
        )

        self.assertRecordValues(
            move_line1, [{"result_package_id": False, "shopfloor_checkout_done": True}],
        )
        self.assertRecordValues(
            move_line2, [{"result_package_id": False, "shopfloor_checkout_done": True}],
        )
        self.assertRecordValues(
            move_line3,
            [{"result_package_id": False, "shopfloor_checkout_done": False}],
        )
        self.assert_response(
            response,
            # go pack to the screen to select lines to put in packages
            next_state="select_line",
            data={"picking": self._stock_picking_data(picking)},
            message={
                "message_type": "success",
                "body": "Product(s) processed as raw product(s)",
            },
        )
