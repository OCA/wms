# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from itertools import product

import mock

from .test_checkout_base import CheckoutCommonCase
from .test_checkout_select_package_base import CheckoutSelectPackageMixin


class CheckoutScanPackageActionCase(CheckoutCommonCase, CheckoutSelectPackageMixin):
    def _test_select_product(
        self, barcode_func, origin_qty_func, expected_qty_func, in_lot=False
    ):
        picking = self._create_picking(
            lines=[(self.product_a, 10), (self.product_b, 10), (self.product_c, 10)]
        )
        for move_line in picking.move_lines:
            # put in 3 different packages
            self._fill_stock_for_moves(move_line, in_package=True, in_lot=in_lot)
        picking.action_assign()

        # we have selected the pack that contains product a
        line_a = picking.move_line_ids[0]
        line_a.qty_done = origin_qty_func(line_a)

        response = self.service.dispatch(
            "scan_package_action",
            params={
                "picking_id": picking.id,
                "selected_line_ids": line_a.ids,
                "barcode": barcode_func(line_a),
            },
        )

        # since we scanned the barcode of the product and we had a
        # qty_done, the qty_done should flip to 0
        self._assert_selected_qties(
            response, line_a, {line_a: expected_qty_func(line_a)}
        )

    def test_scan_package_action_select_product(self):
        self._test_select_product(
            lambda l: l.product_id.barcode, lambda l: l.product_uom_qty, lambda __: 0
        )

    def test_scan_package_action_deselect_product(self):
        self._test_select_product(
            lambda l: l.product_id.barcode, lambda __: 0, lambda l: l.product_uom_qty
        )

    def test_scan_package_action_select_product_packaging(self):
        self._test_select_product(
            lambda l: l.product_id.packaging_ids.barcode,
            lambda l: l.product_uom_qty,
            lambda __: 0,
        )

    def test_scan_package_action_deselect_product_packaging(self):
        self._test_select_product(
            lambda l: l.product_id.packaging_ids.barcode,
            lambda __: 0,
            lambda l: l.product_uom_qty,
        )

    def test_scan_package_action_select_product_lot(self):
        self._test_select_product(
            lambda l: l.lot_id.name,
            lambda __: 0,
            lambda l: l.product_uom_qty,
            in_lot=True,
        )

    def test_scan_package_action_deselect_product_lot(self):
        self._test_select_product(
            lambda l: l.lot_id.name,
            lambda l: l.product_uom_qty,
            lambda __: 0,
            in_lot=True,
        )

    def _test_scan_package_action_scan_product_error_tracked_by(
        self, tracked_by, barcode
    ):
        self.product_a.tracking = tracked_by
        picking = self._create_picking(lines=[(self.product_a, 1)])
        self._fill_stock_for_moves(picking.move_lines, in_package=True)
        picking.action_assign()
        move_line = picking.move_line_ids
        origin_qty_done = move_line.qty_done
        response = self.service.dispatch(
            "scan_package_action",
            params={
                "picking_id": picking.id,
                "selected_line_ids": move_line.ids,
                "barcode": barcode,
            },
        )
        self._assert_selected_qties(
            response,
            move_line,
            # no change as the scan was not valid
            {move_line: origin_qty_done},
            message={
                "message_type": "warning",
                "body": "Product tracked by lot, please scan one.",
            },
        )

    def test_scan_package_action_scan_product_error_tracking(self):
        trackings = ("lot", "serial")
        barcodes = (self.product_a.barcode, self.product_a.packaging_ids.barcode)
        for tracking, barcode in product(trackings, barcodes):
            self._test_scan_package_action_scan_product_error_tracked_by(
                tracking, barcode
            )

    def test_scan_package_action_scan_package_keep_source_package_error(self):
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
        # We'll put only product A and B in the package
        move_line1.qty_done = move_line1.product_uom_qty
        move_line2.qty_done = move_line2.product_uom_qty
        move_line3.qty_done = 0

        response = self.service.dispatch(
            "scan_package_action",
            params={
                "picking_id": picking.id,
                "selected_line_ids": selected_lines.ids,
                # we try to keep the goods in the same package, so we scan the
                # source package but this isn't allowed as it is not a delivery
                # package (i.e. having a delivery packaging set)
                "barcode": pack1.name,
            },
        )

        self.assertRecordValues(
            move_line1,
            [{"result_package_id": pack1.id, "shopfloor_checkout_done": False}],
        )
        self.assertRecordValues(
            move_line2,
            [{"result_package_id": pack1.id, "shopfloor_checkout_done": False}],
        )
        self.assertRecordValues(
            move_line3,
            # qty_done was zero so it hasn't been done anyway
            [{"result_package_id": pack1.id, "shopfloor_checkout_done": False}],
        )
        self.assert_response(
            response,
            # go pack to the screen to select lines to put in packages
            next_state="select_package",
            data={
                "picking": self.data.picking(picking),
                "selected_move_lines": self.data.move_lines(selected_lines),
                "no_package_enabled": not self.service.options.get(
                    "checkout__disable_no_package"
                ),
                "package_allowed": True,
            },
            message=self.service.msg_store.dest_package_not_valid(pack1),
        )

    def test_scan_package_action_scan_package_error_invalid(self):
        picking = self._create_picking(lines=[(self.product_a, 10)])
        move = picking.move_lines
        self._fill_stock_for_moves(move, in_package=True)
        picking.action_assign()

        selected_line = move.move_line_ids
        other_package = self.env["stock.quant.package"].create({})

        response = self.service.dispatch(
            "scan_package_action",
            params={
                "picking_id": picking.id,
                "selected_line_ids": selected_line.ids,
                "barcode": other_package.name,
            },
        )

        self.assertRecordValues(
            selected_line,
            [
                {
                    # the result package must remain identical, so equal to the
                    # source package
                    "result_package_id": selected_line.package_id.id,
                    "shopfloor_checkout_done": False,
                }
            ],
        )
        self._assert_selected_response(
            response,
            selected_line,
            message=self.service.msg_store.dest_package_not_valid(other_package),
        )

    def test_scan_package_action_scan_package_use_existing_package_ok(self):
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

        delivery_packaging = self.env.ref(
            "stock_storage_type.product_product_9_packaging_single_bag"
        )
        package = self.env["stock.quant.package"].create(
            {"packaging_id": delivery_packaging.id}
        )

        # assume that product d was already put in a package,
        # we must be able to put the lines of pack1 inside the same
        pack2_moves.move_line_ids.write(
            {"result_package_id": package.id, "shopfloor_checkout_done": True}
        )

        selected_lines = pack1_moves.move_line_ids
        # they are all selected
        selected_lines.write({"qty_done": 10.0})

        response = self.service.dispatch(
            "scan_package_action",
            params={
                "picking_id": picking.id,
                "selected_line_ids": selected_lines.ids,
                # use the package that was used for product D
                "barcode": package.name,
            },
        )

        self.assertRecordValues(
            selected_lines,
            [
                {"result_package_id": package.id, "shopfloor_checkout_done": True},
                {"result_package_id": package.id, "shopfloor_checkout_done": True},
                {"result_package_id": package.id, "shopfloor_checkout_done": True},
            ],
        )

        self.assert_response(
            response,
            # all the lines are packed, so we expect to go the summary screen
            next_state="summary",
            data={
                "picking": self._stock_picking_data(picking, done=True),
                "all_processed": True,
            },
            message=self.msg_store.goods_packed_in(package),
        )

    def test_scan_package_action_scan_packaging_ok(self):
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

        packaging = (
            self.env["product.packaging"]
            .sudo()
            .create(
                {
                    "name": "Pallet",
                    "barcode": "PPP",
                    "height": 12,
                    "width": 13,
                    "packaging_length": 14,
                }
            )
        )

        response = self.service.dispatch(
            "scan_package_action",
            params={
                "picking_id": picking.id,
                "selected_line_ids": selected_lines.ids,
                # create a new package using this packaging
                "barcode": packaging.barcode,
            },
        )

        new_package = move_line1.result_package_id
        self.assertNotEqual(pack1, new_package)

        self.assertRecordValues(
            new_package,
            [
                {
                    "packaging_id": packaging.id,
                    "pack_length": packaging.packaging_length,
                    "width": packaging.width,
                    "height": packaging.height,
                }
            ],
        )

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
            next_state="select_line",
            data=self._data_for_select_line(picking),
            message=self.msg_store.goods_packed_in(new_package),
        )

    def test_scan_package_action_scan_packaging_bad_carrier(self):
        picking = self._create_picking(lines=[(self.product_a, 10)])
        picking.carrier_id = picking.carrier_id.search([], limit=1)
        pack1_moves = picking.move_lines
        # put in 2 packs, for this test, we'll work on pack1
        self._fill_stock_for_moves(pack1_moves, in_package=True)
        picking.action_assign()
        selected_lines = pack1_moves.move_line_ids
        selected_lines.qty_done = selected_lines.product_uom_qty

        packaging = (
            self.env["product.packaging"]
            .sudo()
            .create(
                {
                    "name": "DeliverX",
                    "barcode": "XXX",
                    "height": 12,
                    "width": 13,
                    "packaging_length": 14,
                }
            )
        )
        # Delivery type and package_carrier_type values
        # depend on specific implementations that we don't have as dependency.
        # What is important here is to simulate their value when mismatching.
        mock1 = mock.patch.object(
            type(packaging),
            "package_carrier_type",
            new_callable=mock.PropertyMock,
        )
        mock2 = mock.patch.object(
            type(picking.carrier_id),
            "delivery_type",
            new_callable=mock.PropertyMock,
        )
        with mock1 as mocked_package_carrier_type, mock2 as mocked_delivery_type:
            # Not matching at all -> bad
            mocked_package_carrier_type.return_value = "DHL"
            mocked_delivery_type.return_value = "UPS"
            response = self.service.dispatch(
                "scan_package_action",
                params={
                    "picking_id": picking.id,
                    "selected_line_ids": selected_lines.ids,
                    # create a new package using this packaging
                    "barcode": packaging.barcode,
                },
            )
            self._assert_selected_response(
                response,
                selected_lines,
                message=self.msg_store.packaging_invalid_for_carrier(
                    packaging, picking.carrier_id
                ),
            )
            # No carrier type set on the packaging -> good
            mocked_package_carrier_type.return_value = "none"
            response = self.service.dispatch(
                "scan_package_action",
                params={
                    "picking_id": picking.id,
                    "selected_line_ids": selected_lines.ids,
                    # create a new package using this packaging
                    "barcode": packaging.barcode,
                },
            )
            self.assertEqual(
                response["message"],
                self.msg_store.goods_packed_in(selected_lines.result_package_id),
            )

    def test_scan_package_action_scan_not_found(self):
        picking = self._create_picking(lines=[(self.product_a, 10)])
        move = picking.move_lines
        self._fill_stock_for_moves(move, in_package=True)
        picking.action_assign()
        selected_line = move.move_line_ids
        response = self.service.dispatch(
            "scan_package_action",
            params={
                "picking_id": picking.id,
                "selected_line_ids": selected_line.ids,
                # create a new package using this packaging
                "barcode": "BARCODE NOT FOUND",
            },
        )
        self._assert_selected_response(
            response,
            selected_line,
            message={"message_type": "error", "body": "Barcode not found"},
        )

    def test_put_in_pack(self):
        picking = self._create_picking(
            lines=[(self.product_a, 10), (self.product_b, 20)]
        )
        self._fill_stock_for_moves(picking.move_lines)
        picking.action_assign()

        # Test that the move lines are marked as 'shopfloor_checkout_done'
        # when putting them in a pack in the backend.
        picking._put_in_pack(picking.move_line_ids)
        self.assertTrue(
            all(line.shopfloor_checkout_done for line in picking.move_line_ids)
        )

        # Check that we return those lines to the frontend.
        res = self.service.dispatch(
            "summary",
            params={
                "picking_id": picking.id,
            },
        )
        returned_lines = res["data"]["summary"]["picking"]["move_lines"]
        expected_line_ids = [line["id"] for line in returned_lines]
        self.assertEqual(expected_line_ids, picking.move_line_ids.ids)
