# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from .test_location_content_transfer_base import LocationContentTransferCommonCase

# pylint: disable=missing-return


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
        cls.shelves = (
            cls.env["stock.location"]
            .sudo()
            .create(
                {
                    "location_id": cls.stock_location.id,
                    "name": "Shelves",
                    "usage": "view",
                }
            )
        )
        (cls.shelf1 | cls.shelf2 | cls.shelf3).sudo().location_id = cls.shelves
        products = (
            cls.product_a
            + cls.product_b
            + cls.product_c
            + cls.product_d
            + cls.product_e
        )
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
        cls.picking3 = cls._create_picking(
            lines=[(cls.product_e, 10)],
        )
        cls.picking3.location_dest_id = cls.shelves
        cls.pickings = picking1 | picking2 | cls.picking3
        cls._fill_stock_for_moves(
            picking1.move_ids, in_package=True, location=cls.content_loc
        )
        cls.product_d_lot = cls.env["stock.lot"].create(
            {"product_id": cls.product_d.id, "company_id": cls.env.company.id}
        )
        cls._fill_stock_for_moves(picking2.move_ids[0], location=cls.content_loc)
        cls._fill_stock_for_moves(
            picking2.move_ids[1], location=cls.content_loc, in_lot=cls.product_d_lot
        )
        # Set Product E in several content locations
        cls._update_qty_in_location(cls.content_loc, cls.product_e, 5.0)
        cls._update_qty_in_location(cls.content_loc_1, cls.product_e, 5.0)
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

    def _scan_package_error(self, package_level, scanned, message):
        response = self.service.dispatch(
            "scan_package",
            params={
                "location_id": self.content_loc.id,
                "package_level_id": package_level.id,
                "barcode": scanned,
            },
        )
        self.assert_response_start_single(response, self.pickings, message=message)

    def test_scan_package_error_wrong_package(self):
        """Wrong package scanned"""
        pack = self.env["stock.quant.package"].sudo().create({})
        self._scan_package_error(
            self.picking1.move_line_ids.package_level_id,
            pack.name,
            {"message_type": "error", "body": "Wrong pack."},
        )

    def test_scan_package_error_wrong_product(self):
        """Wrong product scanned"""
        product = (
            self.env["product.product"]
            .sudo()
            .create(
                {
                    "name": "Wrong",
                    "barcode": "WRONGPRODUCT",
                }
            )
        )
        self._scan_package_error(
            self.picking1.move_line_ids.package_level_id,
            product.barcode,
            {"message_type": "error", "body": "Wrong product."},
        )

    def test_scan_package_error_wrong_lot(self):
        """Wrong product scanned"""
        lot = (
            self.env["stock.lot"]
            .sudo()
            .create(
                {
                    "name": "WRONGLOT",
                    "product_id": self.picking1.move_line_ids[0].product_id.id,
                    "company_id": self.env.company.id,
                }
            )
        )
        self._scan_package_error(
            self.picking1.move_line_ids.package_level_id,
            lot.name,
            {"message_type": "error", "body": "Wrong lot."},
        )

    def test_scan_package_barcode_not_found(self):
        """Nothing found for the barcode"""
        self._scan_package_error(
            self.picking1.move_line_ids.package_level_id,
            "NO_EXISTING_BARCODE",
            {"message_type": "error", "body": "Barcode not found"},
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
        line_product_a.lot_id = self.env["stock.lot"].create(
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
            picking.move_ids, in_package=True, location=self.content_loc
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
        self._fill_stock_for_moves(picking.move_ids, location=self.content_loc)
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
        line_product_a.lot_id = lot = self.env["stock.lot"].create(
            {"product_id": self.product_a.id, "company_id": self.env.company.id}
        )
        picking = self._create_picking(lines=[(self.product_a, 10)])
        self._fill_stock_for_moves(
            picking.move_ids, in_package=True, in_lot=lot, location=self.content_loc
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
        line_product_a.lot_id = lot = self.env["stock.lot"].create(
            {"product_id": self.product_a.id, "company_id": self.env.company.id}
        )
        picking = self._create_picking(lines=[(self.product_a, 10)])
        self._fill_stock_for_moves(
            picking.move_ids, in_lot=lot, location=self.content_loc
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

    def test_scan_line_package_ok(self):
        move_line = self.picking2.move_line_ids[0]
        package = move_line.package_id = self.env["stock.quant.package"].create({})
        self._test_scan_line_ok(move_line, package.name)

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

    def test_scan_line_error_wrong_package(self):
        """Wrong package scanned"""
        move_line = self.picking2.move_line_ids[0]
        pack = self.env["stock.quant.package"].sudo().create({})
        self._test_scan_line_nok(
            self.pickings,
            move_line.id,
            pack.name,
            {"message_type": "error", "body": "Wrong pack."},
        )

    def test_scan_line_error_wrong_product(self):
        """Wrong product scanned"""
        move_line = self.picking2.move_line_ids[0]
        product = (
            self.env["product.product"]
            .sudo()
            .create(
                {
                    "name": "Wrong",
                    "barcode": "WRONGPRODUCT",
                }
            )
        )
        self._test_scan_line_nok(
            self.pickings,
            move_line.id,
            product.barcode,
            {"message_type": "error", "body": "Wrong product."},
        )

    def test_scan_line_error_wrong_lot(self):
        """Wrong product scanned"""
        move_line = self.picking2.move_line_ids[0]
        lot = (
            self.env["stock.lot"]
            .sudo()
            .create(
                {
                    "name": "WRONGLOT",
                    "product_id": move_line.product_id.id,
                    "company_id": self.env.company.id,
                }
            )
        )
        self._test_scan_line_nok(
            self.pickings,
            move_line.id,
            lot.name,
            {"message_type": "error", "body": "Wrong lot."},
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
            response,
            move_lines.mapped("picking_id"),
        )

    def test_postpone_package_ok(self):
        package_level = self.picking1.move_line_ids.package_level_id
        previous_priority = package_level.shopfloor_priority
        self.assertFalse(package_level.shopfloor_postponed)
        response = self.service.dispatch(
            "postpone_package",
            params={
                "location_id": self.content_loc.id,
                "package_level_id": package_level.id,
            },
        )
        self.assertTrue(package_level.shopfloor_postponed)
        self.assertEqual(package_level.shopfloor_priority, previous_priority + 1)
        move_lines = self.service._find_transfer_move_lines(self.content_loc)
        self.assert_response_start_single(
            response,
            move_lines.mapped("picking_id"),
        )

    def test_postpone_sorter(self):
        move_line = self.picking2.move_line_ids[0]
        move_lines = self.service._find_transfer_move_lines(self.content_loc)
        pickings = move_lines.mapped("picking_id")
        sorter = self.service._actions_for("location_content_transfer.sorter")
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
            response,
            move_lines.mapped("picking_id"),
        )

    def test_postpone_line_ok(self):
        move_line = self.picking2.move_line_ids[0]
        previous_priority = move_line.shopfloor_priority
        self.assertFalse(move_line.shopfloor_postponed)
        response = self.service.dispatch(
            "postpone_line",
            params={"location_id": self.content_loc.id, "move_line_id": move_line.id},
        )
        self.assertTrue(move_line.shopfloor_postponed)
        self.assertEqual(move_line.shopfloor_priority, previous_priority + 1)
        move_lines = self.service._find_transfer_move_lines(self.content_loc)
        self.assert_response_start_single(
            response,
            move_lines.mapped("picking_id"),
        )

    def test_postpone_line_ok_with_two_lines_and_view(self):
        """
        Use case:
            - A stock move with two move lines (e.g.: two different source locations)
            - A default destination as a view
            - Postpone the first line
            - Validate the second line
            - Only the first quantity should be transfered
            - The backorder line should be proposed after
        """
        move_line = self.picking3.move_line_ids[0]
        previous_priority = move_line.shopfloor_priority
        self.assertFalse(move_line.shopfloor_postponed)
        response = self.service.dispatch(
            "postpone_line",
            params={"location_id": self.content_loc.id, "move_line_id": move_line.id},
        )
        self.assertTrue(move_line.shopfloor_postponed)
        self.assertEqual(move_line.shopfloor_priority, previous_priority + 1)

        self.assert_response_start_single(response, self.picking3, postponed=True)

        # Select the next line
        move_line = self.picking3.move_line_ids[1]
        previous_priority = move_line.shopfloor_priority
        self.assertFalse(move_line.shopfloor_postponed)

        # Set the destination
        response = self.service.dispatch(
            "set_destination_line",
            params={
                "location_id": self.content_loc.id,
                "move_line_id": move_line.id,
                "quantity": move_line.reserved_uom_qty,
                "barcode": self.shelf1.barcode,
            },
        )
        backorder = self.picking3.backorder_ids
        self.assertTrue(backorder)
        message = {
            "body": "Content transfer to Shelf 1 completed",
            "message_type": "success",
        }

        # Check the backorder is proposed to operator
        self.assert_response_start_single(response, backorder, message=message)

    def test_stock_out_package_wrong_parameters(self):
        """Wrong 'location_id' and 'package_level_id' parameters, redirect the
        user to the 'start' screen.
        """
        package_level = self.picking1.move_line_ids.package_level_id
        response = self.service.dispatch(
            "stock_out_package",
            params={
                "location_id": 1234567890,  # Doesn't exist
                "package_level_id": package_level.id,
            },
        )
        self.assert_response_start(
            response, message=self.service.msg_store.record_not_found()
        )
        response = self.service.dispatch(
            "stock_out_package",
            params={
                "location_id": self.content_loc.id,
                "package_level_id": 1234567890,  # Doesn't exist
            },
        )
        move_lines = self.service._find_transfer_move_lines(self.content_loc)
        self.assert_response_start_single(
            response,
            move_lines.mapped("picking_id"),
        )

    def test_stock_out_package_ok(self):
        """Declare a stock out on a package_level."""
        package_level = self.picking1.move_line_ids.package_level_id
        response = self.service.dispatch(
            "stock_out_package",
            params={
                "location_id": self.content_loc.id,
                "package_level_id": package_level.id,
            },
        )
        move_lines = self.service._find_transfer_move_lines(self.content_loc)
        self.assert_response_start_single(
            response,
            move_lines.mapped("picking_id"),
        )

    def test_stock_out_package_ok_lines_not_owned_by_user(self):
        """Declare a stock out on a package_level with lines not owned by user.

        Same than the previous test, but lines will not be canceled, but
        the assigned user will be removed.

        """
        self.env.user = self.shopfloor_manager
        self.assertTrue(self.env.user != self.picking1.create_uid)
        package_level = self.picking1.move_line_ids.package_level_id
        move_lines_before = self.picking1.move_line_ids
        move_lines_before.shopfloor_user_id = self.env.user
        response = self.service.dispatch(
            "stock_out_package",
            params={
                "location_id": self.content_loc.id,
                "package_level_id": package_level.id,
            },
        )
        move_lines = self.service._find_transfer_move_lines(self.content_loc)
        self.assert_response_start_single(
            response,
            move_lines.mapped("picking_id"),
        )
        self.assertFalse(move_lines_before.exists())

    def test_stock_out_line_wrong_parameters(self):
        """Wrong 'location_id' and 'move_line_id' parameters, redirect the
        user to the 'start' screen.
        """
        move_line = self.picking2.move_line_ids[0]
        response = self.service.dispatch(
            "stock_out_line",
            params={
                "location_id": 1234567890,  # Doesn't exist
                "move_line_id": move_line.id,
            },
        )
        self.assert_response_start(
            response, message=self.service.msg_store.record_not_found()
        )
        response = self.service.dispatch(
            "stock_out_line",
            params={
                "location_id": self.content_loc.id,
                "move_line_id": 1234567890,  # Doesn't exist
            },
        )
        move_lines = self.service._find_transfer_move_lines(self.content_loc)
        self.assert_response_start_single(
            response,
            move_lines.mapped("picking_id"),
        )

    def test_dismiss_package_level_ok(self):
        """Open a package level"""
        package_level = self.picking1.move_line_ids.package_level_id
        move_lines = package_level.move_line_ids
        response = self.service.dispatch(
            "dismiss_package_level",
            params={
                "location_id": self.content_loc.id,
                "package_level_id": package_level.id,
            },
        )
        self.assertFalse(package_level.exists())
        self.assertFalse(move_lines.result_package_id)
        self.assertFalse(move_lines.package_level_id)
        self.assertEqual(move_lines.mapped("shopfloor_priority"), [1, 1])
        move_lines = self.service._find_transfer_move_lines(self.content_loc)
        self.assert_response_start_single(
            response,
            move_lines.mapped("picking_id"),
            message=self.service.msg_store.package_open(),
        )

    def test_dismiss_package_level_error_no_package_level(self):
        """Open a package level, send unknown package level id"""
        response = self.service.dispatch(
            "dismiss_package_level",
            params={"location_id": self.content_loc.id, "package_level_id": 0},
        )
        move_lines = self.service._find_transfer_move_lines(self.content_loc)
        self.assert_response_start_single(
            response,
            move_lines.mapped("picking_id"),
            message=self.service.msg_store.record_not_found(),
        )

    def test_dismiss_package_level_error_no_location(self):
        """Open a package level, send unknown location id"""
        package_level = self.picking1.move_line_ids.package_level_id
        response = self.service.dispatch(
            "dismiss_package_level",
            params={"location_id": 0, "package_level_id": package_level.id},
        )
        self.assert_response_start(
            response,
            message=self.service.msg_store.record_not_found(),
        )


class LocationContentTransferSingleSpecialCase(LocationContentTransferCommonCase):
    """Tests for endpoint used from state start_single (special cases)

    * /stock_out_package
    * /stock_out_line

    """

    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()
        products = cls.product_a | cls.product_b
        for product in products:
            cls.env["stock.putaway.rule"].sudo().create(
                {
                    "product_id": product.id,
                    "location_in_id": cls.stock_location.id,
                    "location_out_id": cls.shelf1.id,
                }
            )

        cls.picking = cls._create_picking(
            lines=[(cls.product_a, 10), (cls.product_b, 10)]
        )
        cls.move_product_a = cls.picking.move_ids.filtered(
            lambda m: m.product_id == cls.product_a
        )
        cls.move_product_b = cls.picking.move_ids.filtered(
            lambda m: m.product_id == cls.product_b
        )
        # Change the initial demand of product_a to get two move lines for
        # reserved qties:
        #   - 10 from the package
        #   - 5 from the qty without package
        cls._fill_stock_for_moves(
            cls.move_product_a, in_package=True, location=cls.content_loc
        )
        cls.move_product_a.product_uom_qty = 15
        cls._update_qty_in_location(
            cls.content_loc,
            cls.product_a,
            5,
        )
        # Put product_b quantities in two different source locations to get
        # two stock move lines (6 and 4 to satisfy 10 qties)
        cls._update_qty_in_location(cls.picking.location_id, cls.product_b, 6)
        cls._update_qty_in_location(cls.content_loc, cls.product_b, 4)
        # Reserve quantities
        cls.picking.action_assign()
        cls._simulate_pickings_selected(cls.picking)

    def test_stock_out_package_split_move(self):
        """Declare a stock out on a package_level related to moves containing
        other unrelated move lines.
        """
        package_level = self.picking.move_line_ids.package_level_id
        self.assertEqual(self.product_a.qty_available, 15)
        response = self.service.dispatch(
            "stock_out_package",
            params={
                "location_id": self.content_loc.id,
                "package_level_id": package_level.id,
            },
        )
        # Check the picking data
        self.assertFalse(package_level.exists())
        moves_product_a = self.picking.move_ids.filtered(
            lambda m: m.product_id == self.product_a
        )
        self.assertEqual(len(moves_product_a), 2)
        move_product_a = moves_product_a.filtered(
            lambda m: m.state not in ("cancel", "done")
        )
        self.assertEqual(len(move_product_a), 1)
        self.assertEqual(move_product_a.state, "assigned")
        self.assertEqual(len(move_product_a.move_line_ids), 1)
        self.assertEqual(self.product_a.qty_available, 5)
        # Check the response
        move_lines = self.service._find_transfer_move_lines(self.content_loc)
        self.assert_response_start_single(
            response,
            move_lines.mapped("picking_id"),
        )

    def test_stock_out_line_split_move(self):
        """Declare a stock out on a move line related to moves containing
        other move lines.
        """
        self.assertEqual(len(self.picking.move_ids), 2)
        self.assertEqual(len(self.move_product_b.move_line_ids), 2)
        move_line = self.move_product_b.move_line_ids.filtered(
            lambda ml: ml.reserved_uom_qty == 4  # 4/10 to stock out
        )
        self.assertEqual(self.product_b.qty_available, 10)
        response = self.service.dispatch(
            "stock_out_line",
            params={"location_id": self.content_loc.id, "move_line_id": move_line.id},
        )
        # Check the picking data
        self.assertFalse(move_line.exists())
        moves_product_b = self.picking.move_ids.filtered(
            lambda m: m.product_id == self.product_b
        )
        self.assertEqual(len(moves_product_b), 2)
        move_product_b = moves_product_b.filtered(
            lambda m: m.state not in ("cancel", "done")
        )
        self.assertEqual(len(move_product_b), 1)
        self.assertEqual(move_product_b.state, "assigned")
        self.assertEqual(len(move_product_b.move_line_ids), 1)

        self.assertEqual(self.product_b.qty_available, 6)
        # Check the response
        move_lines = self.service._find_transfer_move_lines(self.content_loc)
        self.assert_response_start_single(
            response,
            move_lines.mapped("picking_id"),
        )

    def test_stock_out_line_not_created_by_user(self):
        """Declare a stock out on move line not owned by the user.

        This will remove the assigned user but not cancel the move,
        compare to the previous test.

        """
        self.env.user = self.shopfloor_manager
        self.assertTrue(self.env.user != self.picking.create_uid)
        move_line = self.move_product_b.move_line_ids.filtered(
            lambda ml: ml.reserved_uom_qty == 4  # 4/10 to stock out
        )
        move_line.shopfloor_user_id = self.env.user
        self.service.dispatch(
            "stock_out_line",
            params={"location_id": self.content_loc.id, "move_line_id": move_line.id},
        )
        self.assertFalse(move_line.exists())
