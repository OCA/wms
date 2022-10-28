# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from .test_delivery_base import DeliveryCommonCase


class DeliveryScanDeliverCase(DeliveryCommonCase):
    """Tests for /scan_deliver"""

    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()
        cls.product_e.tracking = "lot"
        cls.picking = picking = cls._create_picking(
            lines=[
                # we'll put A and B in a single package
                (cls.product_a, 10),
                (cls.product_b, 10),
                # C alone in a package
                (cls.product_c, 10),
                # D as raw product
                (cls.product_d, 10),
                # E as raw product with a lot
                (cls.product_e, 10),
                # F in two different packages
                (cls.product_f, 10),
            ]
        )
        cls.pack1_moves = picking.move_lines[:2]
        cls.pack2_move = picking.move_lines[2]
        cls.pack3_move = picking.move_lines[5]
        cls.raw_move = picking.move_lines[3]
        cls.raw_lot_move = picking.move_lines[4]
        cls._fill_stock_for_moves(cls.pack1_moves, in_package=True)
        cls._fill_stock_for_moves(cls.pack2_move, in_package=True)
        cls._fill_stock_for_moves(cls.raw_move)
        cls._fill_stock_for_moves(cls.raw_lot_move, in_lot=True)
        # Set a lot for A for the mixed package (A + B)
        cls.product_a_lot = cls.env["stock.production.lot"].create(
            {"product_id": cls.product_a.id, "company_id": cls.env.company.id}
        )
        cls.product_a_quant = cls.env["stock.quant"].search(
            [("product_id", "=", cls.product_a.id)]
        )
        cls.product_a_quant.sudo().lot_id = cls.product_a_lot
        # Fill stock for F moves (two packages)
        for __ in range(2):
            product_f_pkg = cls.env["stock.quant.package"].create({})
            cls._update_qty_in_location(
                cls.pack3_move.location_id,
                cls.pack3_move.product_id,
                5,
                package=product_f_pkg,
            )
        picking.action_assign()
        # Add a packaging on the raw product
        cls.packaging = (
            cls.env["product.packaging"]
            .sudo()
            .create(
                {
                    "name": "TEST PACKAGING",
                    "product_id": cls.raw_move.product_id.id,
                    "qty": 10,
                    "product_uom_id": cls.raw_move.product_id.uom_id.id,
                    "barcode": "TEST_PACKAGING",
                }
            )
        )
        # Some records not related at all to the processed picking
        cls.free_package = cls.env["stock.quant.package"].create(
            {"name": "FREE_PACKAGE"}
        )
        cls.free_lot = cls.env["stock.production.lot"].create(
            {
                "name": "FREE_LOT",
                "product_id": cls.product_a.id,
                "company_id": cls.env.company.id,
            }
        )
        cls.free_product = (
            cls.env["product.product"]
            .sudo()
            .create({"name": "FREE_PRODUCT", "barcode": "FREE_PRODUCT"})
        )

    def test_scan_deliver_scan_picking_ok(self):
        response = self.service.dispatch(
            "scan_deliver",
            params={
                "barcode": self.picking.name,
                "picking_id": None,
                "location_id": None,
            },
        )
        self.assert_response_deliver(response, picking=self.picking)

    def test_scan_deliver_error_barcode_not_found(self):
        response = self.service.dispatch(
            "scan_deliver", params={"barcode": "NO VALID BARCODE", "picking_id": None}
        )
        self.assert_response_deliver(
            response,
            message=self.service.msg_store.barcode_not_found(),
        )

    def test_scan_deliver_error_barcode_not_found_keep_picking(self):
        response = self.service.dispatch(
            "scan_deliver",
            params={"barcode": "NO VALID BARCODE", "picking_id": self.picking.id},
        )
        self.assert_response_deliver(
            response,
            # if the client was working on a picking (it sends picking_id, then
            # send refreshed data)
            picking=self.picking,
            message=self.service.msg_store.barcode_not_found(),
        )

    def _test_scan_set_done_ok(self, move_lines, barcode):
        response = self.service.dispatch("scan_deliver", params={"barcode": barcode})
        self.assert_qty_done(move_lines)
        self.assert_response_deliver(response, picking=self.picking)

    def test_scan_deliver_scan_package_ok(self):
        move_lines = self.pack1_moves.mapped("move_line_ids")
        package = move_lines.mapped("package_id")
        self.assertEqual(self.picking.state, "assigned")
        self._test_scan_set_done_ok(move_lines, package.name)
        self.assertEqual(self.picking.state, "assigned")

    def test_scan_deliver_scan_package_no_move_lines(self):
        response = self.service.dispatch(
            "scan_deliver",
            params={"barcode": self.free_package.name, "picking_id": self.picking.id},
        )
        self.assert_response_deliver(
            response,
            picking=self.picking,
            message=self.service.msg_store.cannot_move_something_in_picking_type(),
        )

    def test_scan_deliver_scan_product_in_package_ok(self):
        self._test_scan_set_done_ok(
            self.pack2_move.mapped("move_line_ids"), self.product_c.barcode
        )

    def test_scan_deliver_scan_product_in_multiple_packages(self):
        response = self.service.dispatch(
            "scan_deliver",
            params={"barcode": self.product_f.barcode, "picking_id": self.picking.id},
        )
        self.assert_response_deliver(
            response,
            picking=self.picking,
            message=self.service.msg_store.product_multiple_packages_scan_package(),
        )

    def test_scan_deliver_scan_product_in_mixed_package(self):
        response = self.service.dispatch(
            "scan_deliver",
            params={"barcode": self.product_a.barcode, "picking_id": self.picking.id},
        )
        self.assert_response_deliver(
            response,
            picking=self.picking,
            message=self.service.msg_store.product_mixed_package_scan_package(),
        )

    def test_scan_deliver_scan_product_tracked_by_lot(self):
        response = self.service.dispatch(
            "scan_deliver",
            params={"barcode": self.product_e.barcode, "picking_id": self.picking.id},
        )
        self.assert_response_deliver(
            response,
            picking=self.picking,
            message=self.service.msg_store.scan_lot_on_product_tracked_by_lot(),
        )

    def test_scan_deliver_scan_raw_product_ok(self):
        self._test_scan_set_done_ok(
            self.raw_move.mapped("move_line_ids"), self.product_d.barcode
        )

    def test_scan_deliver_scan_raw_product_in_multiple_pickings(self):
        # Scan a raw product (not related to a package or lot) which is present
        # in multiple delivery operations (so two different moves).
        # We should be able to process these two moves one after the other.
        picking2 = self._create_picking(
            lines=[
                # D as raw product
                (self.product_d, 10),
            ]
        )
        raw_move2 = picking2.move_lines
        self._fill_stock_for_moves(raw_move2)
        picking2.action_assign()
        # Scan the first move
        self._test_scan_set_done_ok(
            self.raw_move.mapped("move_line_ids"), self.product_d.barcode
        )
        # Scan the second move
        # NOTE: we do not use '_test_scan_set_done_ok' here as we expect
        # the delivery to be complete (we process its only move line).
        response = self.service.dispatch(
            "scan_deliver", params={"barcode": self.product_d.barcode}
        )
        self.assert_response_deliver(
            response, message=self.service.msg_store.transfer_complete(picking2)
        )
        self.assertEqual(raw_move2.quantity_done, 10)
        self.assertEqual(raw_move2.state, "done")

    def test_scan_deliver_scan_product_not_found(self):
        response = self.service.dispatch(
            "scan_deliver", params={"barcode": self.free_product.barcode}
        )
        self.assert_response_deliver(
            response,
            message=self.service.msg_store.product_not_found_in_pickings(),
        )

    def test_scan_deliver_scan_lot_ok(self):
        move_lines = self.raw_lot_move.move_line_ids
        lot = move_lines.lot_id
        self._test_scan_set_done_ok(move_lines, lot.name)

    def test_scan_deliver_scan_lot_not_found(self):
        response = self.service.dispatch("scan_deliver", params={"barcode": "FREE_LOT"})
        self.assert_response_deliver(
            response,
            message=self.service.msg_store.lot_not_found_in_pickings(),
        )

    def test_scan_deliver_scan_lot_in_mixed_package(self):
        response = self.service.dispatch(
            "scan_deliver", params={"barcode": self.product_a_lot.name}
        )
        self.assert_response_deliver(
            response,
            picking=self.picking,
            message=self.service.msg_store.lot_mixed_package_scan_package(),
        )

    def test_scan_deliver_scan_product_packaging_ok(self):
        # Scan a product packaging having the same qty than the qty to ship.
        # We have 10 qties to ship and we scan a product packaging of 10 qties.
        self.menu.sudo().allow_prepackaged_product = True
        line = self.raw_move.mapped("move_line_ids")
        response = self.service.dispatch(
            "scan_deliver", params={"barcode": self.packaging.barcode}
        )
        self.assert_response_deliver(
            response, message=self.service.msg_store.transfer_complete(self.picking)
        )
        self.assertEqual(line.qty_done, self.packaging.qty)

    def test_scan_deliver_scan_product_packaging_partial_qty(self):
        # Scan a product packaging with a smaller qty than the move line
        # We have 10 qties to ship but we scan a product packaging of 5 qties.
        # -> Ship 5 (creating a backorder for the 5 remaining)
        self.menu.sudo().allow_prepackaged_product = True
        self.packaging.qty = 5
        line = self.raw_move.mapped("move_line_ids")
        self.assertEqual(line.move_id.product_qty, 10)
        response = self.service.dispatch(
            "scan_deliver", params={"barcode": self.packaging.barcode}
        )
        self.assert_response_deliver(
            response, message=self.service.msg_store.transfer_complete(self.picking)
        )
        self.assertEqual(line.qty_done, self.packaging.qty)
        self.assertEqual(line.move_id.product_qty, self.packaging.qty)
        self.assertEqual(line.move_id.state, "done")

    def test_scan_deliver_picking_done(self):
        # Set qty done for all lines (packages/raw product/lot...), picking is
        # automatically set to done when the last line is completed
        package1 = self.pack1_moves.mapped("move_line_ids").mapped("package_id")
        package2 = self.pack2_move.mapped("move_line_ids").mapped("package_id")
        self.service.dispatch(
            "set_qty_done_pack",
            params={"package_id": package1.id, "picking_id": self.picking.id},
        )
        self.assertEqual(self.picking.state, "assigned")
        self.service.dispatch(
            "set_qty_done_pack",
            params={"package_id": package2.id, "picking_id": self.picking.id},
        )
        self.assertEqual(self.picking.state, "assigned")
        self.service.dispatch(
            "scan_deliver",
            params={
                "barcode": self.raw_move.product_id.barcode,
                "picking_id": self.picking.id,
            },
        )
        self.assertEqual(self.picking.state, "assigned")
        lot = self.raw_lot_move.move_line_ids.lot_id
        response = self.service.dispatch(
            "scan_deliver",
            params={"barcode": lot.name, "picking_id": self.picking.id},
        )
        self.assertEqual(self.picking.state, "assigned")
        packages_f = self.pack3_move.move_line_ids.mapped("package_id")
        # While all lines are not processed, response still returns the picking
        self.assert_response_deliver(
            response,
            picking=self.picking,
        )
        response = None
        # Once all lines are processed, the last response has no picking returned
        for package in packages_f:
            response = self.service.dispatch(
                "set_qty_done_pack",
                params={"package_id": package.id, "picking_id": self.picking.id},
            )
        self.assertEqual(self.picking.state, "done")
        self.assert_response_deliver(
            response,
            message=self.service.msg_store.transfer_complete(self.picking),
        )


class DeliveryScanDeliverSpecialCase(DeliveryCommonCase):
    """Special cases with different setup for /scan_deliver"""

    def test_scan_deliver_error_picking_wrong_type(self):
        picking = self._create_picking(
            picking_type=self.wh.out_type_id, lines=[(self.product_a, 10)]
        )
        self._fill_stock_for_moves(picking.move_lines, in_package=True)
        picking.action_assign()
        response = self.service.dispatch(
            "scan_deliver", params={"barcode": picking.name}
        )
        self.assert_response_deliver(
            response,
            message={
                "message_type": "error",
                "body": "You cannot move this using this menu.",
            },
        )

    def test_scan_deliver_error_picking_unavailable(self):
        picking = self._create_picking(lines=[(self.product_a, 10)])
        response = self.service.dispatch(
            "scan_deliver", params={"barcode": picking.name}
        )
        self.assert_response_deliver(
            response,
            message={
                "message_type": "error",
                "body": "Transfer {} is not available.".format(picking.name),
            },
        )

    def test_scan_deliver_error_picking_already_done(self):
        picking = self._create_picking(lines=[(self.product_a, 10)])
        self._fill_stock_for_moves(picking.move_lines, in_package=True)
        picking.action_assign()
        picking.move_line_ids.qty_done = picking.move_line_ids.product_uom_qty
        picking._action_done()
        response = self.service.dispatch(
            "scan_deliver", params={"barcode": picking.name}
        )
        self.assert_response_deliver(
            response,
            message={"message_type": "info", "body": "Operation already processed."},
        )
