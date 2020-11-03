# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from .test_checkout_base import CheckoutCommonCase
from .test_checkout_select_package_base import CheckoutSelectPackageMixin


class CheckoutScanLineCase(CheckoutCommonCase, CheckoutSelectPackageMixin):
    def _test_scan_line_ok(self, barcode, selected_lines, packing_info=False):
        """Test /scan_line with a valid return

        :param barcode: the barcode we scan
        :selected_lines: expected move lines returned by the endpoint
        """
        picking = selected_lines.mapped("picking_id")
        response = self.service.dispatch(
            "scan_line", params={"picking_id": picking.id, "barcode": barcode}
        )
        self._assert_selected(response, selected_lines, packing_info=packing_info)

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

    def test_scan_line_package_ok_packing_info(self):
        picking = self._create_picking(
            lines=[(self.product_a, 10), (self.product_b, 10)]
        )
        picking.sudo().partner_id.shopfloor_packing_info = "Please do it like this!"
        picking.sudo().picking_type_id.shopfloor_display_packing_info = True
        move1 = picking.move_lines[0]
        move2 = picking.move_lines[1]
        # put the lines in 2 separate packages (only the first line should be selected
        # by the package barcode)
        self._fill_stock_for_moves(move1, in_package=True)
        self._fill_stock_for_moves(move2, in_package=True)
        picking.action_assign()
        move_line = move1.move_line_ids
        self._test_scan_line_ok(move_line.package_id.name, move_line, packing_info=True)

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
        # do not put them in a package, we'll pack units here
        self._fill_stock_for_moves(picking.move_lines)
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
        self._fill_stock_for_moves(picking.move_lines)
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
        self._fill_stock_for_moves(picking.move_lines)
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

    def test_scan_line_product_in_one_package_all_package_lines_ok(self):
        picking = self._create_picking(
            lines=[(self.product_a, 10), (self.product_b, 10)]
        )
        self._fill_stock_for_moves(picking.move_lines, in_package=True)
        picking.action_assign()
        # Product_a and product_b are in the same package, when we scan product_a,
        # we expect to work on all the lines of the package. If product_a was in
        # more than one package, it would be an error.
        self._test_scan_line_ok(self.product_a.barcode, picking.move_line_ids)

    def _test_scan_line_error(self, picking, barcode, message):
        """Test errors for /scan_line

        :param picking: the picking we are currently working with (selected)
        :param barcode: the barcode we scan
        :param message: the dict of expected error message
        """
        response = self.service.dispatch(
            "scan_line", params={"picking_id": picking.id, "barcode": barcode}
        )
        self.assert_response(
            response,
            next_state="select_line",
            data={"picking": self._stock_picking_data(picking)},
            message=message,
        )

    def test_scan_line_error_barcode_not_found(self):
        picking = self._create_picking(lines=[(self.product_a, 10)])
        self._fill_stock_for_moves(picking.move_lines, in_package=True)
        picking.action_assign()
        self._test_scan_line_error(
            picking,
            "NOT A BARCODE",
            {"message_type": "error", "body": "Barcode not found"},
        )

    def test_scan_line_error_package_not_in_picking(self):
        picking = self._create_picking(lines=[(self.product_a, 10)])
        self._fill_stock_for_moves(picking.move_lines, in_package=True)
        picking2 = self._create_picking(lines=[(self.product_a, 10)])
        self._fill_stock_for_moves(picking2.move_lines, in_package=True)
        (picking | picking2).action_assign()
        package = picking2.move_line_ids.package_id
        # we work with picking, but we scan the package of picking2
        self._test_scan_line_error(
            picking,
            package.name,
            {
                "message_type": "error",
                "body": "Package {} is not in the current transfer.".format(
                    package.name
                ),
            },
        )

    def test_scan_line_error_product_tracked_by_lot(self):
        self.product_a.tracking = "lot"
        picking = self._create_picking(lines=[(self.product_a, 10)])
        self._fill_stock_for_moves(picking.move_lines, in_package=True)
        picking.action_assign()
        # product tracked by lot, but we scan the product barcode, user
        # has to scan the lot
        self._test_scan_line_error(
            picking,
            self.product_a.barcode,
            {
                "message_type": "warning",
                "body": "Product tracked by lot, please scan one.",
            },
        )

    def test_scan_line_error_product_in_two_packages(self):
        picking = self._create_picking(
            lines=[(self.product_a, 10), (self.product_a, 10)],
            # when action_confirm is called, it would merge the moves
            confirm=False,
        )
        self._fill_stock_for_moves(picking.move_lines[0], in_package=True)
        self._fill_stock_for_moves(picking.move_lines[1], in_package=True)
        picking.action_assign()
        self._test_scan_line_error(
            picking,
            self.product_a.barcode,
            {
                "message_type": "warning",
                "body": "This product is part of multiple"
                " packages, please scan a package.",
            },
        )

    def test_scan_line_error_product_in_one_package_and_unit(self):
        picking = self._create_picking(
            lines=[(self.product_a, 10), (self.product_a, 10)],
            # when action_confirm is called, it would merge the moves
            # we want to keep them separated to put a part in a package
            confirm=False,
        )
        # put the product in one package and the other as unit
        self._fill_stock_for_moves(picking.move_lines[0], in_package=True)
        self._fill_stock_for_moves(picking.move_lines[1])
        picking.action_assign()
        self._test_scan_line_error(
            picking,
            self.product_a.barcode,
            {
                "message_type": "warning",
                "body": "This product is part of multiple"
                " packages, please scan a package.",
            },
        )

    def test_scan_line_error_product_not_in_picking(self):
        picking = self._create_picking(lines=[(self.product_a, 10)])
        self._fill_stock_for_moves(picking.move_lines, in_package=True)
        picking.action_assign()
        self._test_scan_line_error(
            picking,
            self.product_b.barcode,
            {
                "message_type": "error",
                "body": "Product is not in the current transfer.",
            },
        )

    def test_scan_line_error_lot_not_in_picking(self):
        picking = self._create_picking(lines=[(self.product_a, 10)])
        self._fill_stock_for_moves(picking.move_lines, in_lot=True)
        picking.action_assign()
        lot = self.env["stock.production.lot"].create(
            {"product_id": self.product_a.id, "company_id": self.env.company.id}
        )
        self._test_scan_line_error(
            picking,
            lot.name,
            {"message_type": "error", "body": "Lot is not in the current transfer."},
        )

    def test_scan_line_error_lot_in_two_packages(self):
        picking = self._create_picking(
            lines=[(self.product_a, 10), (self.product_a, 10)],
            # when action_confirm is called, it would merge the moves
            confirm=False,
        )
        # we want the same lot to be used in 2 lines with different packages
        lot = self.env["stock.production.lot"].create(
            {"product_id": self.product_a.id, "company_id": self.env.company.id}
        )
        self._fill_stock_for_moves(picking.move_lines[0], in_package=True, in_lot=lot)
        self._fill_stock_for_moves(picking.move_lines[1], in_package=True, in_lot=lot)
        picking.action_assign()
        self._test_scan_line_error(
            picking,
            lot.name,
            {
                "message_type": "warning",
                "body": "This lot is part of multiple"
                " packages, please scan a package.",
            },
        )

    def test_scan_line_error_lot_in_one_package_and_unit(self):
        picking = self._create_picking(
            lines=[(self.product_a, 10), (self.product_a, 10)],
            # when action_confirm is called, it would merge the moves
            confirm=False,
        )
        # we want the same lot to be used in 2 lines with different packages
        lot = self.env["stock.production.lot"].create(
            {"product_id": self.product_a.id, "company_id": self.env.company.id}
        )
        self._fill_stock_for_moves(picking.move_lines[0], in_package=True, in_lot=lot)
        self._fill_stock_for_moves(picking.move_lines[1], in_lot=lot)
        picking.action_assign()
        self._test_scan_line_error(
            picking,
            lot.name,
            {
                "message_type": "warning",
                "body": "This lot is part of multiple"
                " packages, please scan a package.",
            },
        )

    def test_scan_line_all_lines_done(self):
        picking = self._create_picking(
            lines=[(self.product_a, 10), (self.product_b, 10)]
        )
        self._fill_stock_for_moves(picking.move_lines, in_package=True)
        picking.action_assign()
        # set all lines as done
        picking.move_line_ids.write({"qty_done": 10.0, "shopfloor_checkout_done": True})
        response = self.service.dispatch(
            "scan_line",
            params={
                "picking_id": picking.id,
                # the barcode doesn't matter as we have no
                # lines to pack anymore
                "barcode": self.product_a.barcode,
            },
        )
        self.assert_response(
            response,
            next_state="summary",
            data={
                "picking": self._stock_picking_data(picking, done=True),
                "all_processed": True,
            },
        )
