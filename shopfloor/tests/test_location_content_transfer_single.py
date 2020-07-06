from .test_location_content_transfer_base import LocationContentTransferCommonCase


class LocationContentTransferSingleCase(LocationContentTransferCommonCase):
    """Tests for endpoint used from state start_single

    * /scan_package
    * /scan_line
    * /postpone_package
    * /postpone_line

    """

    # TODO common with set_destination_all?
    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()
        products = cls.product_a + cls.product_b + cls.product_c + cls.product_d
        for product in products:
            cls.env["stock.putaway.rule"].sudo().create(
                {
                    "product_id": product.id,
                    "location_in_id": cls.stock_location.id,
                    "location_out_id": cls.shelf1.id,
                }
            )

        cls.product_d.tracking = "lot"
        cls.picking1 = picking1 = cls._create_picking(
            lines=[(cls.product_a, 10), (cls.product_b, 10)]
        )
        cls.picking2 = picking2 = cls._create_picking(
            lines=[(cls.product_c, 10), (cls.product_d, 10)]
        )
        cls.pickings = picking1 | picking2
        cls._fill_stock_for_moves(
            picking1.move_lines, in_package=True, location=cls.content_loc
        )
        cls.product_d_lot = cls.env["stock.production.lot"].create(
            {"product_id": cls.product_d.id, "company_id": cls.env.company.id}
        )
        cls._fill_stock_for_moves(picking2.move_lines[0], location=cls.content_loc)
        cls._fill_stock_for_moves(
            picking2.move_lines[1], location=cls.content_loc, in_lot=cls.product_d_lot
        )
        cls.pickings.action_assign()
        cls._simulate_pickings_selected(cls.pickings)

    def _test_scan_package_ok(self, barcode):
        package_level = self.picking1.move_line_ids.package_level_id
        response = self.service.dispatch(
            "scan_package",
            params={
                "location_id": self.content_loc.id,
                "package_level_id": package_level.id,
                "barcode": barcode,
            },
        )
        self.assert_response_scan_destination(response, package_level)

    def test_scan_package_location_not_found(self):
        response = self.service.dispatch(
            "scan_package",
            params={
                "location_id": 1234567890,  # Doesn't exist
                "package_level_id": 42,
                "barcode": "TEST",
            },
        )
        self.assert_response_start(
            response, message=self.service.msg_store.record_not_found()
        )

    def test_scan_package_package_ok(self):
        package_level = self.picking1.move_line_ids.package_level_id
        self._test_scan_package_ok(package_level.package_id.name)

    def test_scan_package_barcode_not_found(self):
        package_level = self.picking1.move_line_ids.package_level_id
        response = self.service.dispatch(
            "scan_package",
            params={
                "location_id": self.content_loc.id,
                "package_level_id": package_level.id,
                "barcode": "NOT_FOUND",
            },
        )
        self.assert_response_start_single(
            response, self.pickings, message=self.service.msg_store.barcode_not_found()
        )

    def test_scan_package_product_ok(self):
        # product_a is in the package and anywhere else so it's
        # accepted to check we scanned the correct package
        self._test_scan_package_ok(self.product_a.barcode)

    def test_scan_package_product_packaging_ok(self):
        # product_a is in the package and anywhere else so it's
        # accepted to check we scanned the correct package
        self._test_scan_package_ok(self.product_a.packaging_ids[0].barcode)

    def test_scan_package_lot_ok(self):
        package_level = self.picking1.move_line_ids.package_level_id
        line_product_a = package_level.move_line_ids[0]
        self.product_a.tracking = "lot"
        line_product_a.lot_id = self.env["stock.production.lot"].create(
            {"product_id": self.product_a.id, "company_id": self.env.company.id}
        )
        # lot of product_a is in the package and anywhere else so it's
        # accepted to check we scanned the correct package
        self._test_scan_package_ok(line_product_a.lot_id.name)

    def _test_scan_package_nok(self, pickings, barcode, message):
        package_level = self.picking1.move_line_ids.package_level_id
        response = self.service.dispatch(
            "scan_package",
            params={
                "location_id": self.content_loc.id,
                "package_level_id": package_level.id,
                "barcode": barcode,
            },
        )
        self.assert_response_start_single(response, pickings, message=message)

    def test_scan_package_product_nok_different_package(self):
        # add another picking with a package with product a,
        # if we scan product A, we can't know for which package it is
        picking = self._create_picking(lines=[(self.product_a, 10)])
        self._fill_stock_for_moves(
            picking.move_lines, in_package=True, location=self.content_loc
        )
        picking.action_assign()
        self._simulate_pickings_selected(picking)
        self._test_scan_package_nok(
            self.pickings | picking,
            self.product_a.barcode,
            {"message_type": "error", "body": "Scan the package"},
        )

    def test_scan_package_product_nok_different_line(self):
        # add another picking with a raw line with product a,
        # if we scan product A, we can't know which line/package we want
        picking = self._create_picking(lines=[(self.product_a, 10)])
        self._fill_stock_for_moves(picking.move_lines, location=self.content_loc)
        picking.action_assign()
        self._simulate_pickings_selected(picking)
        self._test_scan_package_nok(
            self.pickings | picking,
            self.product_a.barcode,
            {"message_type": "error", "body": "Scan the package"},
        )

    def test_scan_package_product_nok_product_tracked(self):
        # we scan product_a's barcode but it's tracked by lot
        self.product_a.tracking = "lot"
        self._test_scan_package_nok(
            self.pickings,
            self.product_a.barcode,
            {"message_type": "error", "body": "Scan the package"},
        )

    def test_scan_package_lot_nok_different_package(self):
        # add another picking with a package with the lot used in our package,
        # if we scan the lot, we can't know for which package it is
        package_level = self.picking1.move_line_ids.package_level_id
        line_product_a = package_level.move_line_ids[0]
        self.product_a.tracking = "lot"
        line_product_a.lot_id = lot = self.env["stock.production.lot"].create(
            {"product_id": self.product_a.id, "company_id": self.env.company.id}
        )
        picking = self._create_picking(lines=[(self.product_a, 10)])
        self._fill_stock_for_moves(
            picking.move_lines, in_package=True, in_lot=lot, location=self.content_loc
        )
        picking.action_assign()
        self._simulate_pickings_selected(picking)
        self._test_scan_package_nok(
            self.pickings | picking,
            self.product_a.barcode,
            {"message_type": "error", "body": "Scan the package"},
        )

    def test_scan_package_lot_nok_different_line(self):
        # add another picking with a raw line with a lot used in our package,
        # if we scan the lot, we can't know which line/package we want
        package_level = self.picking1.move_line_ids.package_level_id
        line_product_a = package_level.move_line_ids[0]
        self.product_a.tracking = "lot"
        line_product_a.lot_id = lot = self.env["stock.production.lot"].create(
            {"product_id": self.product_a.id, "company_id": self.env.company.id}
        )
        picking = self._create_picking(lines=[(self.product_a, 10)])
        self._fill_stock_for_moves(
            picking.move_lines, in_lot=lot, location=self.content_loc
        )
        picking.action_assign()
        self._simulate_pickings_selected(picking)
        self._test_scan_package_nok(
            self.pickings | picking,
            self.product_a.barcode,
            {"message_type": "error", "body": "Scan the package"},
        )

    def test_scan_package_package_level_not_exists(self):
        package_level = self.picking1.move_line_ids.package_level_id
        package_level_id = package_level.id
        package_level.unlink()
        response = self.service.dispatch(
            "scan_package",
            params={
                "location_id": self.content_loc.id,
                "package_level_id": package_level_id,
                "barcode": self.product_a.barcode,
            },
        )
        self.assert_response_start_single(
            response, self.pickings, message=self.service.msg_store.record_not_found()
        )

    def _test_scan_line_ok(self, move_line, barcode):
        response = self.service.dispatch(
            "scan_line",
            params={
                "location_id": self.content_loc.id,
                "move_line_id": move_line.id,
                "barcode": barcode,
            },
        )
        self.assert_response_scan_destination(response, move_line)

    def test_scan_line_product_ok(self):
        move_line = self.picking2.move_line_ids[0]
        # check we selected the good line
        self.assertEqual(move_line.product_id, self.product_c)
        self._test_scan_line_ok(move_line, self.product_c.barcode)

    def test_scan_line_product_packaging_ok(self):
        move_line = self.picking2.move_line_ids[0]
        # check we selected the good line
        self.assertEqual(move_line.product_id, self.product_c)
        self._test_scan_line_ok(move_line, self.product_c.packaging_ids[0].barcode)

    def test_scan_line_lot_ok(self):
        move_line = self.picking2.move_line_ids[1]
        # check we selected the good line (the one with a lot)
        self.assertEqual(move_line.product_id, self.product_d)
        self._test_scan_line_ok(move_line, self.product_d_lot.name)

    def _test_scan_line_nok(self, pickings, move_line_id, barcode, message):
        response = self.service.dispatch(
            "scan_line",
            params={
                "location_id": self.content_loc.id,
                "move_line_id": move_line_id,
                "barcode": barcode,
            },
        )
        self.assert_response_start_single(response, pickings, message=message)

    def test_scan_line_product_nok_product_tracked(self):
        # we scan product_d's barcode but it's tracked by lot
        move_line = self.picking2.move_line_ids[1]
        # check we selected the good line (the one with a lot)
        self.assertEqual(move_line.product_id, self.product_d)
        self._test_scan_line_nok(
            self.pickings,
            move_line.id,
            self.product_d.barcode,
            self.service.msg_store.scan_lot_on_product_tracked_by_lot(),
        )

    def test_scan_line_barcode_not_found(self):
        move_line = self.picking2.move_line_ids[0]
        self._test_scan_line_nok(
            self.pickings,
            move_line.id,
            "NOT_FOUND",
            self.service.msg_store.barcode_not_found(),
        )

    def test_scan_line_move_line_not_exists(self):
        move_line = self.picking2.move_line_ids[0]
        move_line_id = move_line.id
        move_line.unlink()
        self._test_scan_line_nok(
            self.pickings,
            move_line_id,
            "NOT_FOUND",
            self.service.msg_store.record_not_found(),
        )

    def test_postpone_package_wrong_parameters(self):
        """Wrong 'location_id' and 'package_level_id' parameters, redirect the
        user to the 'start' screen.
        """
        package_level = self.picking1.move_line_ids.package_level_id
        response = self.service.dispatch(
            "postpone_package",
            params={
                "location_id": 1234567890,  # Doesn't exist
                "package_level_id": package_level.id,
            },
        )
        self.assert_response_start(
            response, message=self.service.msg_store.record_not_found()
        )
        response = self.service.dispatch(
            "postpone_package",
            params={
                "location_id": self.content_loc.id,
                "package_level_id": 1234567890,  # Doesn't exist
            },
        )
        move_lines = self.service._find_transfer_move_lines(self.content_loc)
        self.assert_response_start_single(
            response, move_lines.mapped("picking_id"),
        )

    def test_postpone_package_ok(self):
        package_level = self.picking1.move_line_ids.package_level_id
        self.assertFalse(package_level.shopfloor_postponed)
        response = self.service.dispatch(
            "postpone_package",
            params={
                "location_id": self.content_loc.id,
                "package_level_id": package_level.id,
            },
        )
        self.assertTrue(package_level.shopfloor_postponed)
        move_lines = self.service._find_transfer_move_lines(self.content_loc)
        self.assert_response_start_single(
            response, move_lines.mapped("picking_id"),
        )

    def test_postpone_sorter(self):
        move_line = self.picking2.move_line_ids[0]
        move_lines = self.service._find_transfer_move_lines(self.content_loc)
        pickings = move_lines.mapped("picking_id")
        sorter = self.service.actions_for("location_content_transfer.sorter")
        sorter.feed_pickings(pickings)
        content_sorted1 = list(sorter)
        self.service.dispatch(
            "postpone_line",
            params={"location_id": self.content_loc.id, "move_line_id": move_line.id},
        )
        sorter.sort()
        content_sorted2 = list(sorter)
        self.assertTrue(content_sorted1 != content_sorted2)

    def test_postpone_line_wrong_parameters(self):
        """Wrong 'location_id' and 'move_line_id' parameters, redirect the
        user to the 'start' screen.
        """
        move_line = self.picking2.move_line_ids[0]
        response = self.service.dispatch(
            "postpone_line",
            params={
                "location_id": 1234567890,  # Doesn't exist
                "move_line_id": move_line.id,
            },
        )
        self.assert_response_start(
            response, message=self.service.msg_store.record_not_found()
        )
        response = self.service.dispatch(
            "postpone_line",
            params={
                "location_id": self.content_loc.id,
                "move_line_id": 1234567890,  # Doesn't exist
            },
        )
        move_lines = self.service._find_transfer_move_lines(self.content_loc)
        self.assert_response_start_single(
            response, move_lines.mapped("picking_id"),
        )

    def test_postpone_line_ok(self):
        move_line = self.picking2.move_line_ids[0]
        self.assertFalse(move_line.shopfloor_postponed)
        response = self.service.dispatch(
            "postpone_line",
            params={"location_id": self.content_loc.id, "move_line_id": move_line.id},
        )
        self.assertTrue(move_line.shopfloor_postponed)
        move_lines = self.service._find_transfer_move_lines(self.content_loc)
        self.assert_response_start_single(
            response, move_lines.mapped("picking_id"),
        )
