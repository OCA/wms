# Copyright 2022 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from .test_checkout_scan_line_base import CheckoutScanLineCaseBase


class CheckoutScanLineNoPrefillQtyCase(CheckoutScanLineCaseBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.menu.sudo().no_prefill_qty = True
        cls.picking = cls._create_picking(
            lines=[(cls.product_a, 3), (cls.product_a, 1), (cls.product_b, 10)],
            confirm=False,
        )
        cls.picking.move_lines._action_confirm(merge=False)
        cls.picking.action_confirm()
        for move in cls.picking.move_lines:
            cls._fill_stock_for_moves(move, in_lot=True)
        cls.picking.action_assign()
        cls.move_lines = cls.picking.move_line_ids

    def _assert_quantity_done(self, barcode, selected_lines, qties):
        picking = selected_lines.mapped("picking_id")
        response = self.service.dispatch(
            "scan_line", params={"picking_id": picking.id, "barcode": barcode}
        )
        response_lines = response["data"]["select_package"]["selected_move_lines"]
        for response_line, qty in zip(response_lines, qties):
            self.assertEqual(response_line["qty_done"], qty)

    def test_scan_line_product_exist_in_two_lines(self):
        """Check scanning a product only increment the quantity done on one line."""
        # All lines are selected because not in a package
        selected_lines = self.picking.move_line_ids
        response = self.service.dispatch(
            "scan_line",
            params={
                "picking_id": self.picking.id,
                "barcode": self.product_a.barcode,
            },
        )
        self._assert_selected_qties(
            response,
            selected_lines,
            {selected_lines[0]: 1, selected_lines[1]: 0, selected_lines[2]: 0},
        )

    def test_scan_line_product_no_prefill_ok(self):
        picking = self._create_picking(
            lines=[(self.product_a, 10), (self.product_b, 10)]
        )
        # do not put them in a package, we'll pack units here
        self._fill_stock_for_moves(picking.move_lines)
        picking.action_assign()
        line_a = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        # When no_prefill_qty is enabled in the checkout menu, prefilled qty
        # should be 1.0 if a product is scanned
        qties = [1.0] * len(line_a)
        self._assert_quantity_done(self.product_a.barcode, line_a, qties)

    def test_scan_line_product_packaging_no_prefill_ok(self):
        picking = self._create_picking(
            lines=[(self.product_a, 10), (self.product_a, 10), (self.product_b, 10)]
        )
        self._fill_stock_for_moves(picking.move_lines)
        picking.action_assign()
        lines_a = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        # When no_prefill_qty is enabled in the checkout menu, prefilled qty
        # should be the packaging qty, if a packaging is scanned
        qties = [3.0] * len(lines_a)
        self._assert_quantity_done(self.product_a_packaging.barcode, lines_a, qties)

    def test_scan_line_product_lot_no_prefill_ok(self):
        picking = self._create_picking(
            lines=[(self.product_a, 1), (self.product_a, 1), (self.product_b, 1)]
        )
        for move in picking.move_lines:
            self._fill_stock_for_moves(move, in_lot=True)
        picking.action_assign()
        first_line = picking.move_line_ids[0]
        lot = first_line.lot_id
        # When no_prefill_qty is enabled in the checkout menu, prefilled qty
        # should be the packaging qty, if a packaging is scanned
        qties = [1.0] * len(first_line)
        self._assert_quantity_done(lot.name, first_line, qties)
