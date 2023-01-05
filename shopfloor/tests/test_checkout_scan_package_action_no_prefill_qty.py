# Copyright 2022 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from .test_checkout_base import CheckoutCommonCase
from .test_checkout_select_package_base import CheckoutSelectPackageMixin


class CheckoutScanPackageActionCaseNoPrefillQty(
    CheckoutCommonCase, CheckoutSelectPackageMixin
):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.menu.sudo().no_prefill_qty = True

    def test_scan_package_action_scan_product_to_increment_qty(self):
        """ """
        picking = self._create_picking(lines=[(self.product_a, 3)])
        self._fill_stock_for_moves(picking.move_lines, in_package=False)
        picking.action_assign()
        move_line = picking.move_line_ids
        origin_qty_done = move_line.qty_done = 2
        response = self.service.dispatch(
            "scan_package_action",
            params={
                "picking_id": picking.id,
                "selected_line_ids": move_line.ids,
                "barcode": move_line.product_id.barcode,
            },
        )
        self._assert_selected_qties(
            response,
            move_line,
            {move_line: origin_qty_done + 1},
        )

    def test_scan_package_action_scan_product2_to_increment_qty(self):
        """Scan a product which is present in two lines.

        Only one line should have its quantity incremented.

        """
        picking = self._create_picking(
            lines=[(self.product_a, 3), (self.product_a, 1)], confirm=False
        )
        picking.move_lines._action_confirm(merge=False)
        picking.action_confirm()
        self._fill_stock_for_moves(picking.move_lines, in_package=False)
        picking.action_assign()
        move_lines = picking.move_line_ids
        response = self.service.dispatch(
            "scan_package_action",
            params={
                "picking_id": picking.id,
                "selected_line_ids": move_lines.ids,
                "barcode": self.product_a.barcode,
            },
        )
        self._assert_selected_qties(
            response,
            move_lines,
            {move_lines[0]: 1, move_lines[1]: 0},
        )

    def test_scan_package_action_scan_lot_to_increment_qty(self):
        """ """
        picking = self._create_picking(lines=[(self.product_a, 3)])
        self._fill_stock_for_moves(picking.move_lines, in_lot=True)
        picking.action_assign()
        move_line = picking.move_line_ids
        origin_qty_done = move_line.qty_done = 2
        response = self.service.dispatch(
            "scan_package_action",
            params={
                "picking_id": picking.id,
                "selected_line_ids": move_line.ids,
                "barcode": move_line.lot_id.name,
            },
        )
        self._assert_selected_qties(
            response,
            move_line,
            {move_line: origin_qty_done + 1},
        )

    def test_scan_package_action_scan_packaging_to_increment_qty(self):
        """ """
        picking = self._create_picking(lines=[(self.product_a, 3)])
        self._fill_stock_for_moves(picking.move_lines, in_package=True, in_lot=False)
        picking.action_assign()
        move_line = picking.move_line_ids
        origin_qty_done = move_line.qty_done = 0
        response = self.service.dispatch(
            "scan_package_action",
            params={
                "picking_id": picking.id,
                "selected_line_ids": move_line.ids,
                "barcode": self.product_a_packaging.barcode,
            },
        )
        self._assert_selected_qties(
            response,
            move_line,
            {move_line: origin_qty_done + self.product_a_packaging.qty},
        )
