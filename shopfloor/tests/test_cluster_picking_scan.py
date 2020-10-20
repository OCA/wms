# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from .test_cluster_picking_base import (
    ClusterPickingCommonCase,
    ClusterPickingLineCommonCase,
)


class ClusterPickingScanLineCase(ClusterPickingLineCommonCase):
    """Tests covering the /scan_line endpoint

    After a batch has been selected and the user confirmed they are
    working on it.

    User scans something and the scan_line endpoints validates they
    scanned the proper thing to pick.
    """

    def _scan_line_ok(self, line, scanned):
        batch = line.picking_id.batch_id
        response = self.service.dispatch(
            "scan_line",
            params={
                "picking_batch_id": batch.id,
                "move_line_id": line.id,
                "barcode": scanned,
            },
        )
        self.assert_response(
            response, next_state="scan_destination", data=self._line_data(line)
        )

    def _scan_line_error(self, line, scanned, message):
        batch = line.picking_id.batch_id
        response = self.service.dispatch(
            "scan_line",
            params={
                "picking_batch_id": batch.id,
                "move_line_id": line.id,
                "barcode": scanned,
            },
        )
        self.assert_response(
            response,
            next_state="start_line",
            data=self._line_data(line),
            message=message,
        )

    def test_scan_line_pack_ok(self):
        """Scan to check if user picks the correct pack for current line"""
        self._simulate_batch_selected(self.batch, in_package=True)
        line = self.batch.picking_ids.move_line_ids
        self._scan_line_ok(line, line.package_id.name)

    def test_scan_line_product_ok(self):
        """Scan to check if user picks the correct product for current line"""
        self._simulate_batch_selected(self.batch)
        line = self.batch.picking_ids.move_line_ids
        self._scan_line_ok(line, line.product_id.barcode)

    def test_scan_line_lot_ok(self):
        """Scan to check if user picks the correct lot for current line"""
        self.product_a.tracking = "lot"
        self._simulate_batch_selected(self.batch, in_lot=True)
        line = self.batch.picking_ids.move_line_ids
        self._scan_line_ok(line, line.lot_id.name)

    def test_scan_line_serial_ok(self):
        """Scan to check if user picks the correct serial for current line"""
        self.product_a.tracking = "serial"
        self._simulate_batch_selected(self.batch, in_lot=True)
        line = self.batch.picking_ids.move_line_ids
        self._scan_line_ok(line, line.lot_id.name)

    def test_scan_line_error_product_tracked(self):
        """Scan a product tracked by lot, must scan the lot"""
        self.product_a.tracking = "lot"
        self._simulate_batch_selected(self.batch, in_lot=True)
        line = self.batch.picking_ids.move_line_ids
        self._scan_line_error(
            line,
            line.product_id.barcode,
            {
                "message_type": "warning",
                "body": "Product tracked by lot, please scan one.",
            },
        )

    def test_scan_line_product_error_several_packages(self):
        """When we scan a product which is in more than one package, error"""
        self._simulate_batch_selected(self.batch, in_package=True)
        line = self.batch.picking_ids.move_line_ids
        # create a second move line for the same product in a different
        # package
        move = line.move_id.copy()
        self._fill_stock_for_moves(move, in_package=True)
        move._action_confirm(merge=False)
        move._action_assign()

        self._scan_line_error(
            line,
            move.product_id.barcode,
            {
                "message_type": "warning",
                "body": "This product is part of multiple"
                " packages, please scan a package.",
            },
        )

    def test_scan_line_product_error_in_one_package_and_unit(self):
        """When we scan a product which is in a package and as raw, error"""
        self._simulate_batch_selected(self.batch, in_package=True)
        line = self.batch.picking_ids.move_line_ids
        # create a second move line for the same product in a different
        # package
        move = line.move_id.copy()
        self._fill_stock_for_moves(move)
        move._action_confirm(merge=False)
        move._action_assign()

        self._scan_line_error(
            line,
            move.product_id.barcode,
            {
                "message_type": "warning",
                "body": "This product is part of multiple"
                " packages, please scan a package.",
            },
        )

    def test_scan_line_lot_error_several_packages(self):
        """When we scan a lot which is in more than one package, error"""
        self._simulate_batch_selected(self.batch, in_package=True, in_lot=True)
        line = self.batch.picking_ids.move_line_ids
        # create a second move line for the same product in a different
        # package
        move = line.move_id.copy()
        self._fill_stock_for_moves(move, in_lot=line.lot_id)
        move._action_confirm(merge=False)
        move._action_assign()

        self._scan_line_error(
            line,
            line.lot_id.name,
            {
                "message_type": "warning",
                "body": "This lot is part of multiple"
                " packages, please scan a package.",
            },
        )

    def test_scan_line_lot_error_in_one_package_and_unit(self):
        """When we scan a lot which is in a package and as raw, error"""
        self._simulate_batch_selected(self.batch, in_package=True, in_lot=True)
        line = self.batch.picking_ids.move_line_ids
        # create a second move line for the same product in a different
        # package
        move = line.move_id.copy()
        self._fill_stock_for_moves(move, in_lot=line.lot_id)
        move._action_confirm(merge=False)
        move._action_assign()
        self._scan_line_error(
            line,
            line.lot_id.name,
            {
                "message_type": "warning",
                "body": "This lot is part of multiple"
                " packages, please scan a package.",
            },
        )

    def test_scan_line_location_ok_single_package(self):
        """Scan to check if user scans a correct location for current line

        If there is only one single package in the location, there is no
        ambiguity so we can use it.
        """
        self._simulate_batch_selected(self.batch, in_package=True)
        line = self.batch.picking_ids.move_line_ids
        self._scan_line_ok(line, line.location_id.barcode)

    def test_scan_line_location_ok_single_product(self):
        """Scan to check if user scans a correct location for current line

        If there is only one single product in the location, there is no
        ambiguity so we can use it.
        """
        self._simulate_batch_selected(self.batch)
        line = self.batch.picking_ids.move_line_ids
        self._scan_line_ok(line, line.location_id.barcode)

    def test_scan_line_location_ok_single_lot(self):
        """Scan to check if user scans a correct location for current line

        If there is only one single lot in the location, there is no
        ambiguity so we can use it.
        """
        self._simulate_batch_selected(self.batch, in_lot=True)
        line = self.batch.picking_ids.move_line_ids
        self._scan_line_ok(line, line.location_id.barcode)

    def test_scan_line_location_error_several_package(self):
        """Scan to check if user scans a correct location for current line

        If there are several packages in the location, user has to scan one.
        """
        self._simulate_batch_selected(self.batch, in_package=True)
        line = self.batch.picking_ids.move_line_ids
        location = line.location_id
        # add a second package in the location
        self._update_qty_in_location(
            location,
            self.product_b,
            10,
            package=self.env["stock.quant.package"].create({}),
        )
        self._scan_line_error(
            line,
            location.barcode,
            {
                "message_type": "warning",
                "body": "Several packages found in Stock, please scan a package.",
            },
        )

    def test_scan_line_location_error_several_products(self):
        """Scan to check if user scans a correct location for current line

        If there are several products in the location, user has to scan one.
        """
        self._simulate_batch_selected(self.batch)
        line = self.batch.picking_ids.move_line_ids
        location = line.location_id
        # add a second product in the location
        self._update_qty_in_location(location, self.product_b, 10)
        self._scan_line_error(
            line,
            location.barcode,
            {
                "message_type": "warning",
                "body": "Several products found in Stock, please scan a product.",
            },
        )

    def test_scan_line_location_error_several_lots(self):
        """Scan to check if user scans a correct location for current line

        If there are several lots in the location, user has to scan one.
        """
        self._simulate_batch_selected(self.batch, in_lot=True)
        line = self.batch.picking_ids.move_line_ids
        location = line.location_id
        lot = self.env["stock.production.lot"].create(
            {"product_id": self.product_a.id, "company_id": self.env.company.id}
        )
        # add a second lot in the location
        self._update_qty_in_location(location, self.product_a, 10, lot=lot)
        self._scan_line_error(
            line,
            location.barcode,
            {
                "message_type": "warning",
                "body": "Several lots found in Stock, please scan a lot.",
            },
        )

    def test_scan_line_error_not_found(self):
        """Nothing found for the barcode"""
        self._simulate_batch_selected(self.batch, in_package=True)
        self._scan_line_error(
            self.batch.picking_ids.move_line_ids,
            "NO_EXISTING_BARCODE",
            {"message_type": "error", "body": "Barcode not found"},
        )


class ClusterPickingScanDestinationPackCase(ClusterPickingCommonCase):
    """Tests covering the /scan_destination_pack endpoint

    After a batch has been selected and the user confirmed they are
    working on it, user picked the good, now they scan the location
    destination.
    """

    @classmethod
    def setUpClassBaseData(cls, *args, **kwargs):
        super().setUpClassBaseData(*args, **kwargs)
        cls.batch = cls._create_picking_batch(
            [
                [
                    cls.BatchProduct(product=cls.product_a, quantity=10),
                    cls.BatchProduct(product=cls.product_b, quantity=10),
                ],
                [cls.BatchProduct(product=cls.product_a, quantity=10)],
            ]
        )
        cls.one_line_picking = cls.batch.picking_ids.filtered(
            lambda picking: len(picking.move_lines) == 1
        )
        cls.two_lines_picking = cls.batch.picking_ids.filtered(
            lambda picking: len(picking.move_lines) == 2
        )

        cls.bin1 = cls.env["stock.quant.package"].create({})
        cls.bin2 = cls.env["stock.quant.package"].create({})

        cls._simulate_batch_selected(cls.batch)

    def test_scan_destination_pack_ok(self):
        """Happy path for scan destination package

        It sets the line in the pack for the full qty
        """
        line = self.batch.picking_ids.move_line_ids[0]
        next_line = self.batch.picking_ids.move_line_ids[1]
        qty_done = line.product_uom_qty
        response = self.service.dispatch(
            "scan_destination_pack",
            params={
                "picking_batch_id": self.batch.id,
                "move_line_id": line.id,
                "barcode": self.bin1.name,
                "quantity": qty_done,
            },
        )
        self.assertRecordValues(
            line, [{"qty_done": qty_done, "result_package_id": self.bin1.id}]
        )
        self.assert_response(
            response,
            next_state="start_line",
            data=self._line_data(next_line),
            message={
                "message_type": "success",
                "body": "{} {} put in {}".format(
                    line.qty_done, line.product_id.display_name, self.bin1.name
                ),
            },
        )

    def test_scan_destination_pack_ok_last_line(self):
        """Happy path for scan destination package

        It sets the line in the pack for the full qty
        """
        self._set_dest_package_and_done(self.one_line_picking.move_line_ids, self.bin1)
        self._set_dest_package_and_done(
            self.two_lines_picking.move_line_ids[0], self.bin2
        )
        # this is the only remaining line to pick
        line = self.two_lines_picking.move_line_ids[1]
        qty_done = line.product_uom_qty
        response = self.service.dispatch(
            "scan_destination_pack",
            params={
                "picking_batch_id": self.batch.id,
                "move_line_id": line.id,
                "barcode": self.bin2.name,
                "quantity": qty_done,
            },
        )
        self.assertRecordValues(
            line, [{"qty_done": qty_done, "result_package_id": self.bin2.id}]
        )
        data = self._data_for_batch(self.batch, self.packing_location)
        self.assert_response(
            response,
            # they reach the same destination so next state unload_all
            next_state="unload_all",
            data=data,
        )

    def test_scan_destination_pack_not_empty_same_picking(self):
        """Scan a destination package with move lines of same picking"""
        line1 = self.two_lines_picking.move_line_ids[0]
        line2 = self.two_lines_picking.move_line_ids[1]
        # we already scan and put the first line in bin1
        self._set_dest_package_and_done(line1, self.bin1)
        response = self.service.dispatch(
            "scan_destination_pack",
            params={
                "picking_batch_id": self.batch.id,
                "move_line_id": line2.id,
                # this bin is used for the same picking, should be allowed
                "barcode": self.bin1.name,
                "quantity": line2.product_uom_qty,
            },
        )
        self.assert_response(
            response,
            next_state="start_line",
            # we did not pick this line, so it should go there
            data=self._line_data(self.one_line_picking.move_line_ids),
            message=self.ANY,
        )

    def test_scan_destination_pack_not_empty_different_picking(self):
        """Scan a destination package with move lines of other picking"""
        # do as if the user already picked the first good (for another picking)
        # and put it in bin1
        self._set_dest_package_and_done(self.one_line_picking.move_line_ids, self.bin1)
        line = self.two_lines_picking.move_line_ids[0]
        response = self.service.dispatch(
            "scan_destination_pack",
            params={
                "picking_batch_id": self.batch.id,
                "move_line_id": line.id,
                # this bin is used for the other picking
                "barcode": self.bin1.name,
                "quantity": line.product_uom_qty,
            },
        )
        self.assertRecordValues(line, [{"qty_done": 0, "result_package_id": False}])
        self.assert_response(
            response,
            next_state="scan_destination",
            data=self._line_data(line),
            message={
                "message_type": "error",
                "body": "The destination bin {} is not empty,"
                " please take another.".format(self.bin1.name),
            },
        )

    def test_scan_destination_pack_bin_not_found(self):
        """Scan a destination package that do not exist"""
        line = self.one_line_picking.move_line_ids
        response = self.service.dispatch(
            "scan_destination_pack",
            params={
                "picking_batch_id": self.batch.id,
                "move_line_id": line.id,
                # this bin is used for the other picking
                "barcode": "⌿",
                "quantity": line.product_uom_qty,
            },
        )
        self.assert_response(
            response,
            next_state="scan_destination",
            data=self._line_data(line),
            message={
                "message_type": "error",
                "body": "Bin {} doesn't exist".format("⌿"),
            },
        )

    def test_scan_destination_pack_quantity_more(self):
        """Pick more units than expected"""
        line = self.one_line_picking.move_line_ids
        response = self.service.dispatch(
            "scan_destination_pack",
            params={
                "picking_batch_id": self.batch.id,
                "move_line_id": line.id,
                "barcode": self.bin1.name,
                "quantity": line.product_uom_qty + 1,
            },
        )
        self.assert_response(
            response,
            next_state="scan_destination",
            data=self._line_data(line),
            message={
                "message_type": "error",
                "body": "You must not pick more than {} units.".format(
                    line.product_uom_qty
                ),
            },
        )

    def test_scan_destination_pack_quantity_less(self):
        """Pick less units than expected"""
        line = self.one_line_picking.move_line_ids
        quant = self.env["stock.quant"].search(
            [
                ("location_id", "=", line.location_id.id),
                ("product_id", "=", line.product_id.id),
            ]
        )
        quant.ensure_one()
        self.assertRecordValues(quant, [{"quantity": 40.0, "reserved_quantity": 20.0}])

        # when we pick less quantity than expected, the line is split
        # and the user is proposed to pick the next line for the remaining
        # quantity
        response = self.service.dispatch(
            "scan_destination_pack",
            params={
                "picking_batch_id": self.batch.id,
                "move_line_id": line.id,
                "barcode": self.bin1.name,
                "quantity": line.product_uom_qty - 3,
            },
        )
        new_line = self.one_line_picking.move_line_ids - line

        self.assert_response(
            response,
            next_state="start_line",
            data=self._line_data(new_line),
            message={
                "message_type": "success",
                "body": "{} {} put in {}".format(
                    line.qty_done, line.product_id.display_name, self.bin1.name
                ),
            },
        )

        self.assertRecordValues(
            line,
            [{"qty_done": 7, "result_package_id": self.bin1.id, "product_uom_qty": 7}],
        )
        self.assertRecordValues(
            new_line,
            [{"qty_done": 0, "result_package_id": False, "product_uom_qty": 3}],
        )
        # the reserved quantity on the quant must stay the same
        self.assertRecordValues(quant, [{"quantity": 40.0, "reserved_quantity": 20.0}])

    def test_scan_destination_pack_zero_check_activated(self):
        """Location will be emptied, have to go to zero check"""
        # ensure that the location used for the test will contain only what we want
        self.zero_check_location = (
            self.env["stock.location"]
            .sudo()
            .create(
                {
                    "name": "ZeroCheck",
                    "location_id": self.stock_location.id,
                    "barcode": "ZEROCHECK",
                }
            )
        )
        line = self.one_line_picking.move_line_ids
        location, product, qty = (
            self.zero_check_location,
            line.product_id,
            line.product_uom_qty,
        )
        self.one_line_picking.do_unreserve()

        # ensure we have activated the zero check
        self.one_line_picking.picking_type_id.sudo().shopfloor_zero_check = True
        # Update the quantity in the location to be equal to the line's
        # so when scan_destination_pack sets the qty_done, the planned
        # qty should be zero and trigger a zero check
        self._update_qty_in_location(location, product, qty)
        # Reserve goods (now the move line has the expected source location)
        self.one_line_picking.move_lines.location_id = location
        self.one_line_picking.action_assign()
        line = self.one_line_picking.move_line_ids
        response = self.service.dispatch(
            "scan_destination_pack",
            params={
                "picking_batch_id": self.batch.id,
                "move_line_id": line.id,
                "barcode": self.bin1.name,
                "quantity": line.product_uom_qty,
            },
        )

        self.assert_response(
            response,
            next_state="zero_check",
            data={
                "id": line.id,
                "location_src": self.data.location(line.location_id),
                "batch": self.data.picking_batch(self.batch),
            },
        )

    def test_scan_destination_pack_zero_check_disabled(self):
        """Location will be emptied, no zero check, continue"""
        line = self.one_line_picking.move_line_ids
        # ensure we have deactivated the zero check
        self.one_line_picking.picking_type_id.sudo().shopfloor_zero_check = False
        # Update the quantity in the location to be equal to the line's
        # so when scan_destination_pack sets the qty_done, the planned
        # qty should be zero and trigger a zero check
        self._update_qty_in_location(
            line.location_id, line.product_id, line.product_uom_qty
        )
        response = self.service.dispatch(
            "scan_destination_pack",
            params={
                "picking_batch_id": self.batch.id,
                "move_line_id": line.id,
                "barcode": self.bin1.name,
                "quantity": line.product_uom_qty,
            },
        )

        next_line = self.two_lines_picking.move_line_ids[0]
        # continue to the next one, no zero check
        self.assert_response(
            response,
            next_state="start_line",
            data=self._line_data(next_line),
            message={
                "message_type": "success",
                "body": "{} {} put in {}".format(
                    line.qty_done, line.product_id.display_name, self.bin1.name
                ),
            },
        )


class ClusterPickingIsZeroCase(ClusterPickingCommonCase):
    """Tests covering the /is_zero endpoint

    After a line has been scanned, if the location is empty, the
    client application is redirected to the "zero_check" state,
    where the user has to confirm or not that the location is empty.
    When the location is empty, there is nothing to do, but when it
    in fact not empty, a draft inventory must be created for the
    product so someone can verify.
    """

    @classmethod
    def setUpClassBaseData(cls, *args, **kwargs):
        super().setUpClassBaseData(*args, **kwargs)
        cls.batch = cls._create_picking_batch(
            [
                [
                    cls.BatchProduct(product=cls.product_a, quantity=10),
                    cls.BatchProduct(product=cls.product_b, quantity=10),
                ]
            ]
        )
        cls.picking = cls.batch.picking_ids
        cls._simulate_batch_selected(cls.batch)

        cls.line = cls.picking.move_line_ids[0]
        cls.next_line = cls.picking.move_line_ids[1]
        cls.bin1 = cls.env["stock.quant.package"].create({})
        cls._update_qty_in_location(
            cls.line.location_id, cls.line.product_id, cls.line.product_uom_qty
        )
        # we already scan and put the first line in bin1, at this point the
        # system see the location is empty and reach "zero_check"
        cls._set_dest_package_and_done(cls.line, cls.bin1)

    def test_is_zero_is_empty(self):
        """call /is_zero confirming it's empty"""
        response = self.service.dispatch(
            "is_zero",
            params={
                "picking_batch_id": self.batch.id,
                "move_line_id": self.line.id,
                "zero": True,
            },
        )
        self.assert_response(
            response,
            next_state="start_line",
            data=self._line_data(self.next_line),
            message={
                "message_type": "success",
                "body": "{} {} put in {}".format(
                    self.line.qty_done,
                    self.line.product_id.display_name,
                    self.bin1.name,
                ),
            },
        )

    def test_is_zero_is_not_empty(self):
        """call /is_zero not confirming it's empty"""
        response = self.service.dispatch(
            "is_zero",
            params={
                "picking_batch_id": self.batch.id,
                "move_line_id": self.line.id,
                "zero": False,
            },
        )
        inventory = self.env["stock.inventory"].search(
            [
                ("location_ids", "in", self.line.location_id.id),
                ("product_ids", "in", self.line.product_id.id),
                ("state", "=", "draft"),
            ]
        )
        self.assertTrue(inventory)
        self.assertEqual(
            inventory.name,
            "Zero check issue on location Stock ({})".format(self.picking.name),
        )
        self.assert_response(
            response,
            next_state="start_line",
            data=self._line_data(self.next_line),
            message={
                "message_type": "success",
                "body": "{} {} put in {}".format(
                    self.line.qty_done,
                    self.line.product_id.display_name,
                    self.bin1.name,
                ),
            },
        )
