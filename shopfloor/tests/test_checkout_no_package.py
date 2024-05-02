# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import werkzeug

from odoo import fields

from .test_checkout_base import CheckoutCommonCase
from .test_checkout_select_package_base import CheckoutSelectPackageMixin


# pylint: disable=missing-return
class CheckoutNoPackageCase(CheckoutCommonCase, CheckoutSelectPackageMixin):
    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()
        cls.picking = picking = cls._create_picking(
            lines=[
                (cls.product_a, 10),
                (cls.product_b, 10),
                (cls.product_c, 10),
                (cls.product_d, 10),
            ]
        )
        cls.pack1_moves = pack1_moves = picking.move_ids[:3]
        cls.pack2_moves = pack2_moves = picking.move_ids[3:]
        # put in 2 packs, for this test, we'll work on pack1
        cls._fill_stock_for_moves(pack1_moves)
        cls._fill_stock_for_moves(pack2_moves)
        picking.action_assign()

    def test_no_package_ok(self):
        move_line1, move_line2, move_line3 = self.pack1_moves.move_line_ids
        selected_lines = move_line1 + move_line2

        # we'll put only the first 2 lines (product A and B) w/ no package
        move_line1.qty_done = move_line1.reserved_uom_qty
        move_line2.qty_done = move_line2.reserved_uom_qty
        move_line3.qty_done = 0
        response = self.service.dispatch(
            "no_package",
            params={
                "picking_id": self.picking.id,
                "selected_line_ids": selected_lines.ids,
            },
        )

        self.assertRecordValues(
            move_line1,
            [{"result_package_id": False, "shopfloor_checkout_done": True}],
        )
        self.assertRecordValues(
            move_line2,
            [{"result_package_id": False, "shopfloor_checkout_done": True}],
        )
        self.assertRecordValues(
            move_line3,
            [{"result_package_id": False, "shopfloor_checkout_done": False}],
        )
        self.assert_response(
            response,
            # go pack to the screen to select lines to put in packages
            next_state="select_line",
            data=self._data_for_select_line(self.picking),
            message={
                "message_type": "success",
                "body": "Product(s) processed as raw product(s)",
            },
        )

    def test_no_package_disabled(self):
        self.service.work.options = {"checkout__disable_no_package": True}
        with self.assertRaises(werkzeug.exceptions.BadRequest) as err:
            self.service.dispatch(
                "no_package",
                params={
                    "picking_id": self.picking.id,
                    "selected_line_ids": self.pack1_moves.move_line_ids.ids,
                },
            )
            self.assertEqual(repr(err), "`checkout.no_package` endpoint is not enabled")

    def test_set_dest_package_error_qty_done_above(self):
        # If the qty_done of a selected line goes beyond
        # the maximum allowed, a message should be displayed
        # and the user shouldn't be allowed to select a package.
        line = fields.first(self.picking.move_line_ids)
        line.qty_done = line.reserved_uom_qty + 1
        response = self.service.dispatch(
            "list_dest_package",
            params={
                "picking_id": self.picking.id,
                "selected_line_ids": self.picking.move_line_ids.ids,
            },
        )
        self._assert_select_package_qty_above(response, self.picking)
