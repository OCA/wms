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
        response = self.service.dispatch(
            "scan_line", params={"move_line_id": line.id, "barcode": scanned}
        )
        self.assert_response(
            response, next_state="scan_destination", data=self._line_data(line)
        )

    def _scan_line_error(self, line, scanned, message):
        response = self.service.dispatch(
            "scan_line", params={"move_line_id": line.id, "barcode": scanned}
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
                "message": "Product tracked by lot, please scan one.",
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
                "message": "Several packages found in Stock, please scan a package.",
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
                "message": "Several products found in Stock, please scan a product.",
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
                "message": "Several lots found in Stock, please scan a lot.",
            },
        )

    def test_scan_line_error_not_found(self):
        """Nothing found for the barcode"""
        self._simulate_batch_selected(self.batch, in_package=True)
        self._scan_line_error(
            self.batch.picking_ids.move_line_ids,
            "NO_EXISTING_BARCODE",
            {"message_type": "error", "message": "Barcode not found"},
        )


class ClusterPickingScanDestinationPackCase(ClusterPickingCommonCase):
    """Tests covering the /scan_destination_pack endpoint

    After a batch has been selected and the user confirmed they are
    working on it, user picked the good, now they scan the location
    destination.
    """

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)
        cls.batch = cls._create_picking_batch(
            [
                [
                    cls.BatchProduct(product=cls.product_a, quantity=10),
                    cls.BatchProduct(product=cls.product_b, quantity=10),
                ],
                [cls.BatchProduct(product=cls.product_a, quantity=10)],
            ]
        )
        cls.one_line_picking = cls.batch.picking_ids[0]
        cls.two_lines_picking = cls.batch.picking_ids[1]

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
                "message": "{} {} put in {}".format(
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
                "move_line_id": line.id,
                "barcode": self.bin2.name,
                "quantity": qty_done,
            },
        )
        self.assertRecordValues(
            line, [{"qty_done": qty_done, "result_package_id": self.bin2.id}]
        )
        self.assert_response(
            response,
            # they reach the same destination so next state unload_all
            next_state="unload_all",
            data={
                "id": self.batch.id,
                "name": self.batch.name,
                "location_dst": {
                    "id": self.packing_location.id,
                    "name": self.packing_location.name,
                },
            },
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
                "message": "The destination bin {} is not empty,"
                " please take another.".format(self.bin1.name),
            },
        )

    def test_scan_destination_pack_bin_not_found(self):
        """Scan a destination package that do not exist"""
        line = self.one_line_picking.move_line_ids
        response = self.service.dispatch(
            "scan_destination_pack",
            params={
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
                "message": "Bin {} doesn't exist".format("⌿"),
            },
        )

    def test_scan_destination_pack_quantity_more(self):
        """Pick more units than expected"""
        line = self.one_line_picking.move_line_ids
        response = self.service.dispatch(
            "scan_destination_pack",
            params={
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
                "message": "You must not pick more than {} units.".format(
                    line.product_uom_qty
                ),
            },
        )

    def test_scan_destination_pack_quantity_less(self):
        """Pick less units than expected"""
        line = self.one_line_picking.move_line_ids
        response = self.service.dispatch(
            "scan_destination_pack",
            params={
                "move_line_id": line.id,
                "barcode": self.bin1.name,
                "quantity": line.product_uom_qty - 3,
            },
        )

        self.assertRecordValues(
            line,
            [{"qty_done": 7, "result_package_id": self.bin1.id, "product_uom_qty": 7}],
        )
        new_line = self.one_line_picking.move_line_ids - line
        self.assertRecordValues(
            new_line,
            [{"qty_done": 0, "result_package_id": False, "product_uom_qty": 3}],
        )

        self.assert_response(
            response,
            next_state="start_line",
            # TODO ensure the duplicated line is the next line, it works now but
            # maybe only by chance
            data=self._line_data(new_line),
            message={
                "message_type": "success",
                "message": "{} {} put in {}".format(
                    line.qty_done, line.product_id.display_name, self.bin1.name
                ),
            },
        )

    def test_scan_destination_pack_zero_check(self):
        """Location will be emptied, have to go to zero check"""
        line = self.one_line_picking.move_line_ids
        # Update the quantity in the location to be equal to the line's
        # so when scan_destination_pack sets the qty_done, the planned
        # qty should be zero and trigger a zero check
        self._update_qty_in_location(
            line.location_id, line.product_id, line.product_uom_qty
        )
        response = self.service.dispatch(
            "scan_destination_pack",
            params={
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
                "location_src": {
                    "id": line.location_id.id,
                    "name": line.location_id.name,
                },
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
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)
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
            "is_zero", params={"move_line_id": self.line.id, "zero": True}
        )
        self.assert_response(
            response,
            next_state="start_line",
            data=self._line_data(self.next_line),
            message={
                "message_type": "success",
                "message": "{} {} put in {}".format(
                    self.line.qty_done,
                    self.line.product_id.display_name,
                    self.bin1.name,
                ),
            },
        )

    def test_is_zero_is_not_empty(self):
        """call /is_zero not confirming it's empty"""
        response = self.service.dispatch(
            "is_zero", params={"move_line_id": self.line.id, "zero": False}
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
                "message": "{} {} put in {}".format(
                    self.line.qty_done,
                    self.line.product_id.display_name,
                    self.bin1.name,
                ),
            },
        )
