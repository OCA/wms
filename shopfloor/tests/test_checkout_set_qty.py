# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from .test_checkout_base import CheckoutCommonCase
from .test_checkout_select_package_base import CheckoutSelectPackageMixin


class CheckoutSetQtyCommonCase(CheckoutCommonCase, CheckoutSelectPackageMixin):
    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()
        picking = cls._create_picking(
            lines=[(cls.product_a, 10), (cls.product_b, 10), (cls.product_c, 10)]
        )
        cls.moves_pack1 = picking.move_lines[:2]
        cls.moves_pack2 = picking.move_lines[2:]
        cls._fill_stock_for_moves(cls.moves_pack1, in_package=True)
        cls._fill_stock_for_moves(cls.moves_pack2, in_package=True)
        picking.action_assign()
        cls.picking = picking

    def setUp(self):
        super().setUp()
        # we assume we have called /select_line on pack one, so by default, we
        # expect the lines for product a and b to have their qty_done set to
        # their product_uom_qty at the start of the tests
        self.selected_lines = self.moves_pack1.move_line_ids
        self.deselected_lines = self.moves_pack2.move_line_ids
        self.service._select_lines(self.selected_lines)
        self.assertTrue(
            all(l.qty_done == l.product_uom_qty for l in self.selected_lines)
        )
        self.assertTrue(all(l.qty_done == 0 for l in self.deselected_lines))


class CheckoutResetLineQtyCase(CheckoutSetQtyCommonCase):
    def test_reset_line_qty_ok(self):
        selected_lines = self.moves_pack1.move_line_ids
        line_to_reset = selected_lines[0]
        line_with_qty = selected_lines[1]
        # we want to check that when we give the package id, we get
        # all its move lines
        response = self.service.dispatch(
            "reset_line_qty",
            params={
                "picking_id": self.picking.id,
                "selected_line_ids": selected_lines.ids,
                "move_line_id": line_to_reset.id,
            },
        )
        self._assert_selected_qties(
            response,
            selected_lines,
            {line_to_reset: 0, line_with_qty: line_with_qty.product_uom_qty},
        )

    def test_reset_line_qty_not_found(self):
        selected_lines = self.moves_pack1.move_line_ids
        response = self.service.dispatch(
            "reset_line_qty",
            params={
                "picking_id": self.picking.id,
                "selected_line_ids": selected_lines.ids,
                "move_line_id": 0,
            },
        )
        # if the move line is not found, ignore and return to the
        # screen
        self._assert_selected_qties(
            response,
            selected_lines,
            {line: line.product_uom_qty for line in selected_lines},
            message={
                "body": "The record you were working on does not exist anymore.",
                "message_type": "error",
            },
        )


class CheckoutSetLineQtyCase(CheckoutSetQtyCommonCase):
    def test_set_line_qty_ok(self):
        selected_lines = self.moves_pack1.move_line_ids
        # do as if the user removed the qties of the 2 selected lines
        selected_lines.qty_done = 0
        line_to_set = selected_lines[0]
        line_no_qty = selected_lines[1]
        # we want to check that when we give the package id, we get
        # all its move lines
        response = self.service.dispatch(
            "set_line_qty",
            params={
                "picking_id": self.picking.id,
                "selected_line_ids": selected_lines.ids,
                "move_line_id": line_to_set.id,
            },
        )
        self.assertEqual(line_to_set.qty_done, line_to_set.product_uom_qty)
        self.assertEqual(line_no_qty.qty_done, 0)
        self._assert_selected_qties(
            response,
            selected_lines,
            {line_to_set: line_to_set.product_uom_qty, line_no_qty: 0},
        )

    def test_set_line_qty_not_found(self):
        selected_lines = self.moves_pack1.move_line_ids
        response = self.service.dispatch(
            "set_line_qty",
            params={
                "picking_id": self.picking.id,
                "selected_line_ids": selected_lines.ids,
                "move_line_id": 0,
            },
        )
        # if the move line is not found, ignore and return to the
        # screen
        self._assert_selected_qties(
            response,
            selected_lines,
            {line: line.product_uom_qty for line in selected_lines},
            message={
                "body": "The record you were working on does not exist anymore.",
                "message_type": "error",
            },
        )


class CheckoutSetCustomQtyCase(CheckoutSetQtyCommonCase):
    def test_set_custom_qty_ok(self):
        selected_lines = self.moves_pack1.move_line_ids
        line_to_change = selected_lines[0]
        line_keep_qty = selected_lines[1]
        # Process full qty
        new_qty = line_to_change.product_uom_qty
        # we want to check that when we give the package id, we get
        # all its move lines
        response = self.service.dispatch(
            "set_custom_qty",
            params={
                "picking_id": self.picking.id,
                "selected_line_ids": selected_lines.ids,
                "move_line_id": line_to_change.id,
                "qty_done": new_qty,
            },
        )
        self.assertEqual(line_to_change.qty_done, new_qty)
        self.assertEqual(line_keep_qty.qty_done, line_keep_qty.product_uom_qty)
        self._assert_selected_qties(
            response,
            selected_lines,
            {line_to_change: new_qty, line_keep_qty: line_keep_qty.product_uom_qty},
        )

    def test_set_custom_qty_not_found(self):
        selected_lines = self.moves_pack1.move_line_ids
        response = self.service.dispatch(
            "set_custom_qty",
            params={
                "picking_id": self.picking.id,
                "selected_line_ids": selected_lines.ids,
                "move_line_id": 0,
                "qty_done": 3,
            },
        )
        # if the move line is not found, ignore and return to the
        # screen
        self._assert_selected_qties(
            response,
            selected_lines,
            {line: line.product_uom_qty for line in selected_lines},
            message={
                "body": "The record you were working on does not exist anymore.",
                "message_type": "error",
            },
        )

    def test_set_custom_qty_above(self):
        selected_lines = self.moves_pack1.move_line_ids
        line1 = selected_lines[0]
        # modify so we can check that a too high quantity set the max
        line1.qty_done = 1
        line2 = selected_lines[1]
        response = self.service.dispatch(
            "set_custom_qty",
            params={
                "picking_id": self.picking.id,
                "selected_line_ids": selected_lines.ids,
                "move_line_id": line1.id,
                "qty_done": line1.product_uom_qty + 1,
            },
        )
        self._assert_selected_qties(
            response,
            selected_lines,
            {line1: line1.product_uom_qty, line2: line2.product_uom_qty},
            message={
                "body": "Not allowed to pack more than the quantity, "
                "the value has been changed to the maximum.",
                "message_type": "warning",
            },
        )

    def test_set_custom_qty_negative(self):
        selected_lines = self.moves_pack1.move_line_ids
        line1 = selected_lines[0]
        line2 = selected_lines[1]
        response = self.service.dispatch(
            "set_custom_qty",
            params={
                "picking_id": self.picking.id,
                "selected_line_ids": selected_lines.ids,
                "move_line_id": line1.id,
                "qty_done": -1,
            },
        )
        self._assert_selected_qties(
            response,
            selected_lines,
            {line1: line1.product_uom_qty, line2: line2.product_uom_qty},
            message={
                "body": "Negative quantity not allowed.",
                "message_type": "error",
            },
        )

    def test_set_custom_qty_partial(self):
        selected_lines = self.moves_pack1.move_line_ids
        line_to_change = selected_lines[0]
        line_keep_qty = selected_lines[1]
        # split 1 qty
        new_qty = line_to_change.product_uom_qty - 1
        response = self.service.dispatch(
            "set_custom_qty",
            params={
                "picking_id": self.picking.id,
                "selected_line_ids": selected_lines.ids,
                "move_line_id": line_to_change.id,
                "qty_done": new_qty,
            },
        )
        self.assertEqual(line_to_change.qty_done, new_qty)
        self.assertEqual(line_keep_qty.qty_done, line_keep_qty.product_uom_qty)
        new_line = [
            x for x in self.moves_pack1.move_line_ids if x not in selected_lines
        ][0]
        self.assertEqual(new_line.product_uom_qty, 1.0)
        self._assert_selected_qties(
            response,
            self.moves_pack1.move_line_ids,
            {
                line_to_change: new_qty,
                line_keep_qty: line_keep_qty.product_uom_qty,
                new_line: 0.0,
            },
        )
