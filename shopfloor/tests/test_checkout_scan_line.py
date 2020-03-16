from .test_checkout_base import CheckoutCommonCase


class CheckoutScanLineCase(CheckoutCommonCase):
    def _test_scan_line_ok(self, barcode, selected_lines):
        picking = selected_lines.mapped("picking_id")
        response = self.service.dispatch(
            "scan_line", params={"picking_id": picking.id, "barcode": barcode}
        )
        for line in selected_lines:
            self.assertEqual(
                line.qty_done,
                line.product_uom_qty,
                "Scanned lines must have their qty done set to the reserved quantity",
            )
        self.assert_response(
            response,
            next_state="select_package",
            data={
                "selected_move_lines": [
                    self._move_line_data(ml) for ml in selected_lines
                ],
                "picking": {
                    "id": picking.id,
                    "name": picking.name,
                    "note": "",
                    "origin": "",
                    "line_count": 2,
                    "partner": {"id": self.customer.id, "name": self.customer.name},
                },
            },
        )

    def test_scan_line_package_ok(self):
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

    def test_scan_line_package_several_lines_ok(self):
        picking = self._create_picking(
            lines=[(self.product_a, 10), (self.product_b, 10)]
        )
        # put all the lines in the same source package
        self._fill_stock_for_moves(picking.move_lines, in_package=True)
        picking.action_assign()
        package = picking.move_line_ids.mapped("package_id")
        self._test_scan_line_ok(package.name, picking.move_line_ids)

    def test_scan_line_product_ok(self):
        picking = self._create_picking(
            lines=[(self.product_a, 10), (self.product_b, 10)]
        )
        self._fill_stock_for_moves(picking.move_lines, in_package=True)
        picking.action_assign()
        line_a = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        # we have 2 different products in the picking, we scan the first
        # one and expect to select the line
        self._test_scan_line_ok(self.product_a.barcode, line_a)

    def test_scan_line_product_several_lines_ok(self):
        picking = self._create_picking(
            lines=[(self.product_a, 10), (self.product_a, 10), (self.product_b, 10)]
        )
        self._fill_stock_for_moves(picking.move_lines, in_package=True)
        picking.action_assign()
        lines_a = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        # expect to select all the lines with the scanned product, as long
        # as they are in the same package
        self._test_scan_line_ok(self.product_a.barcode, lines_a)

    def test_scan_line_product_packaging_ok(self):
        picking = self._create_picking(
            lines=[(self.product_a, 10), (self.product_a, 10), (self.product_b, 10)]
        )
        self._fill_stock_for_moves(picking.move_lines, in_package=True)
        picking.action_assign()
        lines_a = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        # when we scan the packaging of the product, we should select the
        # lines as if the product was scanned
        self._test_scan_line_ok(self.product_a_packaging.barcode, lines_a)

    def test_scan_line_product_lot_ok(self):
        picking = self._create_picking(
            lines=[(self.product_a, 1), (self.product_a, 1), (self.product_b, 1)]
        )
        for move in picking.move_lines:
            self._fill_stock_for_moves(move, in_lot=True)
        picking.action_assign()
        first_line = picking.move_line_ids[0]
        lot = first_line.lot_id
        self._test_scan_line_ok(lot.name, first_line)

    # TODO test 2 lines with product in different packages
    # TODO test 2 lines with lots in different packages
