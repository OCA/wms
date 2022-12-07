# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.addons.shopfloor.tests.test_checkout_scan_line_base import (
    CheckoutScanLineCaseBase,
)

GS1_BARCODE = "(01)09506000117843(11)141231(10)1234AB"
PROD_BARCODE = "09506000117843"
LOT_BARCODE = "1234AB"

# TODO: we use `search.find` only in checkout.scan_line for now
# but we should test all the other endpoint and scenario as well
# after moving them to `find`.


class CheckoutScanLineCase(CheckoutScanLineCaseBase):
    def test_scan_line_package_ok(self):
        # NOTE: packages GS1 barcode are not supported yet
        # -> we test the std behavior
        picking = self._create_picking(
            lines=[(self.product_a, 10), (self.product_b, 10)]
        )
        move1 = picking.move_lines[0]
        move2 = picking.move_lines[1]
        # put the lines in 2 separate packages (only the first line should be selected
        # by the package barcode)
        self._fill_stock_for_moves(move1, in_package=True)
        self._fill_stock_for_moves(move2, in_package=True)
        picking.action_assign()
        move_line = move1.move_line_ids
        self._test_scan_line_ok(move_line.package_id.name, move_line)

    def test_scan_line_product_ok(self):
        picking = self._create_picking(
            lines=[(self.product_a, 10), (self.product_b, 10)]
        )
        # do not put them in a package, we'll pack units here
        self._fill_stock_for_moves(picking.move_lines)
        picking.action_assign()
        line_a = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        # we have 2 different products in the picking, we scan the first
        # one and expect to select the line
        self.product_a.barcode = PROD_BARCODE
        self._test_scan_line_ok(GS1_BARCODE, line_a)

    def test_scan_line_product_lot_ok(self):
        picking = self._create_picking(
            lines=[(self.product_a, 1), (self.product_a, 1), (self.product_b, 1)]
        )
        for move in picking.move_lines:
            self._fill_stock_for_moves(move, in_lot=True)
        picking.action_assign()
        first_line = picking.move_line_ids[0]
        lot = first_line.lot_id
        lot.name = LOT_BARCODE
        self._test_scan_line_ok(GS1_BARCODE, first_line)

    def test_scan_line_product_serial_ok(self):
        barcode = "(11)141231(21)1234AB"
        picking = self._create_picking(
            lines=[(self.product_a, 1), (self.product_a, 1), (self.product_b, 1)]
        )
        for move in picking.move_lines:
            self._fill_stock_for_moves(move, in_lot=True)
        picking.action_assign()
        first_line = picking.move_line_ids[0]
        lot = first_line.lot_id
        lot.name = LOT_BARCODE
        self._test_scan_line_ok(barcode, first_line)
