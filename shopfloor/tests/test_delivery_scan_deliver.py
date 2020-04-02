from .test_delivery_base import DeliveryCommonCase


class DeliveryScanDeliverCase(DeliveryCommonCase):
    """Tests for /scan_deliver"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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
            ]
        )
        cls.pack1_moves = picking.move_lines[:2]
        cls.pack2_move = picking.move_lines[2]
        cls.raw_move = picking.move_lines[3]
        cls.raw_lot_move = picking.move_lines[4]
        cls._fill_stock_for_moves(cls.pack1_moves, in_package=True)
        cls._fill_stock_for_moves(cls.pack2_move, in_package=True)
        cls._fill_stock_for_moves(cls.raw_move)
        cls._fill_stock_for_moves(cls.raw_lot_move, in_lot=True)
        picking.action_assign()

    def test_scan_deliver_scan_picking_ok(self):
        response = self.service.dispatch(
            "scan_deliver", params={"barcode": self.picking.name, "picking_id": None}
        )
        self.assert_response_deliver(response, picking=self.picking)

    def test_scan_deliver_error_barcode_not_found(self):
        response = self.service.dispatch(
            "scan_deliver", params={"barcode": "NO VALID BARCODE", "picking_id": None}
        )
        self.assert_response_deliver(
            response, message={"message_type": "error", "message": "Barcode not found"}
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
            message={"message_type": "error", "message": "Barcode not found"},
        )

    def assert_qty_done(self, move_lines):
        self.assertRecordValues(
            move_lines, [{"qty_done": line.product_uom_qty} for line in move_lines]
        )
        package_level = move_lines.package_level_id
        if package_level:
            # we have a package level only when there is a package
            self.assertRecordValues(package_level, [{"is_done": True}])

    def _test_scan_set_done_ok(self, move_lines, barcode):
        response = self.service.dispatch("scan_deliver", params={"barcode": barcode})
        self.assert_qty_done(move_lines)
        self.assert_response_deliver(response, picking=self.picking)

    def test_scan_deliver_scan_package_ok(self):
        move_lines = self.pack1_moves.mapped("move_line_ids")
        package = move_lines.mapped("package_id")
        self._test_scan_set_done_ok(move_lines, package.name)

    def test_scan_deliver_scan_product_in_package_ok(self):
        self._test_scan_set_done_ok(
            self.pack2_move.mapped("move_line_ids"), self.product_c.barcode
        )

    def test_scan_deliver_scan_raw_product_ok(self):
        self._test_scan_set_done_ok(
            self.raw_move.mapped("move_line_ids"), self.product_d.barcode
        )

    def test_scan_deliver_scan_lot_ok(self):
        move_lines = self.raw_lot_move.move_line_ids
        lot = move_lines.lot_id
        self._test_scan_set_done_ok(move_lines, lot.name)

    # TODO test for product in different packages
    # TODO test for product in one package but the package contains a product
    # in different packages


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
                "message": "You cannot move this using this menu.",
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
                "message": "Transfer {} is not available.".format(picking.name),
            },
        )

    def test_scan_deliver_error_picking_already_done(self):
        picking = self._create_picking(lines=[(self.product_a, 10)])
        self._fill_stock_for_moves(picking.move_lines, in_package=True)
        picking.action_assign()
        picking.move_line_ids.qty_done = picking.move_line_ids.product_uom_qty
        picking.action_done()
        response = self.service.dispatch(
            "scan_deliver", params={"barcode": picking.name}
        )
        self.assert_response_deliver(
            response,
            message={"message_type": "info", "message": "Operation already processed."},
        )
