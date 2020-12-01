# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from .test_cluster_picking_base import ClusterPickingCommonCase


class ClusterPickingUnloadingCommonCase(ClusterPickingCommonCase):
    @classmethod
    def setUpClassBaseData(cls, *args, **kwargs):
        super().setUpClassBaseData(*args, **kwargs)

        # activate the computation of this field, so we have a chance to
        # transition to the 'show completion info' popup.
        cls.picking_type.sudo().display_completion_info = True

        cls.batch = cls._create_picking_batch(
            [
                [
                    cls.BatchProduct(product=cls.product_a, quantity=10),
                    cls.BatchProduct(product=cls.product_b, quantity=10),
                ],
                [cls.BatchProduct(product=cls.product_a, quantity=10)],
            ]
        )
        cls._simulate_batch_selected(cls.batch)

        cls.one_line_picking = cls.batch.picking_ids.filtered(
            lambda picking: len(picking.move_lines) == 1
        )
        cls.two_lines_picking = cls.batch.picking_ids.filtered(
            lambda picking: len(picking.move_lines) == 2
        )
        two_lines_product_a = cls.two_lines_picking.move_line_ids.filtered(
            lambda line: line.product_id == cls.product_a
        )
        two_lines_product_b = cls.two_lines_picking.move_line_ids - two_lines_product_a
        # force order of move lines to use in tests
        cls.move_lines = (
            cls.one_line_picking.move_line_ids
            + two_lines_product_a
            + two_lines_product_b
        )

        cls.bin1 = cls.env["stock.quant.package"].create({})
        cls.bin2 = cls.env["stock.quant.package"].create({})
        cls.packing_a_location = (
            cls.env["stock.location"]
            .sudo()
            .create(
                {
                    "name": "Packing A",
                    "barcode": "Packing-A",
                    "location_id": cls.packing_location.id,
                }
            )
        )
        cls.packing_b_location = (
            cls.env["stock.location"]
            .sudo()
            .create(
                {
                    "name": "Packing B",
                    "barcode": "Packing-B",
                    "location_id": cls.packing_location.id,
                }
            )
        )


class ClusterPickingPrepareUnloadCase(ClusterPickingUnloadingCommonCase):
    """Tests covering the /prepare_unload endpoint

    Destination packages have been set on all the move lines of the batch.
    The unload operation will start, but we have 2 paths for this:

    1. unload all the destination packages at the same place
    2. unload the destination packages one by one at different places

    By default, if all the move lines have the same destination, the
    first path is used. A flag on the batch picking keeps track of which
    path is used.
    """

    def test_prepare_unload_all_same_dest(self):
        """All move lines have the same destination location"""
        move_lines = self.move_lines
        self._set_dest_package_and_done(move_lines[:2], self.bin1)
        self._set_dest_package_and_done(move_lines[2:], self.bin2)
        move_lines.write({"location_dest_id": self.packing_location.id})
        response = self.service.dispatch(
            "prepare_unload", params={"picking_batch_id": self.batch.id}
        )
        location = self.packing_location
        data = self._data_for_batch(self.batch, location)
        self.assert_response(
            response,
            next_state="unload_all",
            data=data,
        )

    def test_prepare_unload_different_dest(self):
        """All move lines have different destination locations"""
        move_lines = self.move_lines
        self._set_dest_package_and_done(move_lines[:2], self.bin1)
        self._set_dest_package_and_done(move_lines[2:], self.bin2)
        move_lines[:2].write({"location_dest_id": self.packing_a_location.id})
        move_lines[2:].write({"location_dest_id": self.packing_b_location.id})
        response = self.service.dispatch(
            "prepare_unload", params={"picking_batch_id": self.batch.id}
        )
        first_line = move_lines[0]
        location = first_line.location_dest_id
        data = self._data_for_batch(self.batch, location, pack=self.bin1)
        self.assert_response(
            response,
            next_state="unload_single",
            data=data,
        )


class ClusterPickingSetDestinationAllCase(ClusterPickingUnloadingCommonCase):
    """Tests covering the /set_destination_all endpoint

    All the picked lines go to the same destination, a single call to this
    endpoint set them as "unloaded" and set the destination. When the last
    available line of a picking is unloaded, the picking is set to 'done'.
    """

    def test_set_destination_all_ok(self):
        """Set destination on all lines for the full batch and end the process"""
        move_lines = self.move_lines
        # put destination packages, the whole quantity on lines and a similar
        # destination (when /set_destination_all is called, all the lines to
        # unload must have the same destination)
        self._set_dest_package_and_done(move_lines[:2], self.bin1)
        self._set_dest_package_and_done(move_lines[2:], self.bin2)
        move_lines.write({"location_dest_id": self.packing_location.id})

        response = self.service.dispatch(
            "set_destination_all",
            params={
                "picking_batch_id": self.batch.id,
                "barcode": self.packing_location.barcode,
            },
        )
        # since the whole batch is complete, we expect the batch and all
        # pickings to be 'done'
        self.assertRecordValues(
            move_lines.mapped("picking_id"), [{"state": "done"}, {"state": "done"}]
        )
        self.assertRecordValues(
            move_lines,
            [
                {
                    "shopfloor_unloaded": True,
                    "qty_done": 10,
                    "state": "done",
                    "location_dest_id": self.packing_location.id,
                },
                {
                    "shopfloor_unloaded": True,
                    "qty_done": 10,
                    "state": "done",
                    "location_dest_id": self.packing_location.id,
                },
                {
                    "shopfloor_unloaded": True,
                    "qty_done": 10,
                    "state": "done",
                    "location_dest_id": self.packing_location.id,
                },
            ],
        )
        self.assertRecordValues(self.batch, [{"state": "done"}])
        self.assert_response(
            response,
            next_state="start",
            message={"message_type": "success", "body": "Batch Transfer complete"},
        )

    def test_set_destination_all_remaining_lines(self):
        """Set destination on all lines for a part of the batch"""
        # Put destination packages, the whole quantity on lines and a similar
        # destination (when /set_destination_all is called, all the lines to
        # unload must have the same destination).
        # However, we keep a line without qty_done and destination package,
        # so when the dest location is set, the endpoint should route back
        # to the 'start_line' state to work on the remaining line.
        lines_to_unload = self.move_lines[:2]
        self._set_dest_package_and_done(lines_to_unload, self.bin1)
        lines_to_unload.write({"location_dest_id": self.packing_location.id})

        response = self.service.dispatch(
            "set_destination_all",
            params={
                "picking_batch_id": self.batch.id,
                "barcode": self.packing_location.barcode,
            },
        )
        # Since the whole batch is not complete, state should not be done.
        # The picking with one line should be "done" because we unloaded its line.
        # The second one still has a line to pick.
        self.assertRecordValues(self.one_line_picking, [{"state": "done"}])
        self.assertRecordValues(self.two_lines_picking, [{"state": "assigned"}])
        self.assertRecordValues(
            self.move_lines,
            [
                {
                    "shopfloor_unloaded": True,
                    "qty_done": 10,
                    "state": "done",
                    "picking_id": self.one_line_picking.id,
                    "location_dest_id": self.packing_location.id,
                },
                {
                    "shopfloor_unloaded": True,
                    "qty_done": 10,
                    # will be done when the second line of the picking is unloaded
                    "state": "assigned",
                    "picking_id": self.two_lines_picking.id,
                    "location_dest_id": self.packing_location.id,
                },
                {
                    "shopfloor_unloaded": False,
                    "qty_done": 0,
                    "state": "assigned",
                    "picking_id": self.two_lines_picking.id,
                    "location_dest_id": self.packing_location.id,
                },
            ],
        )
        self.assertRecordValues(self.batch, [{"state": "in_progress"}])

        self.assert_response(
            # the remaining move line still needs to be picked
            response,
            next_state="start_line",
            data=self._line_data(self.move_lines[2]),
            message={"body": "Batch Transfer line done", "message_type": "success"},
        )

    def test_set_destination_all_picking_unassigned(self):
        """Set destination on lines for some transfers of the batch.

        The remaining transfers stay as unavailable (confirmed) and are removed
        from the batch when this one is validated.
        The remaining transfers will be processed later in a new batch.
        """
        self.batch.picking_ids.do_unreserve()
        location = self.one_line_picking.location_id
        product = self.one_line_picking.move_lines.product_id
        qty = self.one_line_picking.move_lines.product_uom_qty
        self._update_qty_in_location(location, product, qty)
        self.one_line_picking.action_assign()
        # Prepare lines to process
        lines = self.one_line_picking.move_line_ids
        self._set_dest_package_and_done(lines, self.bin1)
        lines.write({"location_dest_id": self.packing_location.id})

        response = self.service.dispatch(
            "set_destination_all",
            params={
                "picking_batch_id": self.batch.id,
                "barcode": self.packing_location.barcode,
            },
        )
        # The batch should be done with only one picking.
        # The remaining picking has been removed from the current batch
        self.assertRecordValues(self.one_line_picking, [{"state": "done"}])
        self.assertRecordValues(self.two_lines_picking, [{"state": "confirmed"}])
        self.assertRecordValues(self.batch, [{"state": "done"}])
        self.assertEqual(self.one_line_picking.batch_id, self.batch)
        self.assertFalse(self.two_lines_picking.batch_id)

        self.assert_response(
            response,
            next_state="start",
            message=self.service.msg_store.batch_transfer_complete(),
        )

    def test_set_destination_all_but_different_dest(self):
        """Endpoint was called but destinations are different"""
        move_lines = self.move_lines
        self._set_dest_package_and_done(move_lines, self.bin1)
        move_lines[:2].write({"location_dest_id": self.packing_a_location.id})
        move_lines[2:].write({"location_dest_id": self.packing_b_location.id})

        response = self.service.dispatch(
            "set_destination_all",
            params={
                "picking_batch_id": self.batch.id,
                "barcode": self.packing_location.barcode,
            },
        )
        location = move_lines[0].location_dest_id
        data = self._data_for_batch(self.batch, location, pack=self.bin1)
        self.assert_response(
            response,
            next_state="unload_single",
            data=data,
        )

    def test_set_destination_all_error_location_not_found(self):
        """Endpoint called with a barcode not existing for a location"""
        move_lines = self.move_lines
        self._set_dest_package_and_done(move_lines, self.bin1)
        move_lines.write({"location_dest_id": self.packing_a_location.id})

        response = self.service.dispatch(
            "set_destination_all",
            params={"picking_batch_id": self.batch.id, "barcode": "NOTFOUND"},
        )
        location = move_lines[0].location_dest_id
        data = self._data_for_batch(self.batch, location)
        self.assert_response(
            response,
            next_state="unload_all",
            data=data,
            message={
                "message_type": "error",
                "body": "No location found for this barcode.",
            },
        )

    def test_set_destination_all_error_location_invalid(self):
        """Endpoint called with a barcode for an invalid location

        It is invalid when the location is not the destination location or
        sublocation of the picking type.
        """
        move_lines = self.move_lines
        self._set_dest_package_and_done(move_lines, self.bin1)
        move_lines.write({"location_dest_id": self.packing_a_location.id})

        response = self.service.dispatch(
            "set_destination_all",
            params={
                "picking_batch_id": self.batch.id,
                "barcode": self.dispatch_location.barcode,
            },
        )
        location = move_lines[0].location_dest_id
        data = self._data_for_batch(self.batch, location)
        self.assert_response(
            response,
            next_state="unload_all",
            data=data,
            message={"message_type": "error", "body": "You cannot place it here"},
        )

    def test_set_destination_all_error_location_move_invalid(self):
        """Endpoint called with a barcode for an invalid location

        It is invalid when the location is not a sublocation of the picking
        or move destination
        """
        move_lines = self.move_lines
        self._set_dest_package_and_done(move_lines, self.bin1)
        move_lines[0].move_id.location_dest_id = self.packing_a_location
        move_lines[0].picking_id.location_dest_id = self.packing_a_location

        response = self.service.dispatch(
            "set_destination_all",
            params={
                "picking_batch_id": self.batch.id,
                "barcode": self.packing_b_location.barcode,
            },
        )
        location = move_lines[0].location_dest_id
        data = self._data_for_batch(self.batch, location)
        self.assert_response(
            response,
            next_state="unload_all",
            data=data,
            message=self.service.msg_store.dest_location_not_allowed(),
        )

    def test_set_destination_all_need_confirmation(self):
        """Endpoint called with a barcode for another (valid) location"""
        move_lines = self.move_lines
        self._set_dest_package_and_done(move_lines, self.bin1)
        move_lines.write({"location_dest_id": self.packing_a_location.id})

        response = self.service.dispatch(
            "set_destination_all",
            params={
                "picking_batch_id": self.batch.id,
                "barcode": self.packing_b_location.barcode,
            },
        )
        location = move_lines[0].location_dest_id
        data = self._data_for_batch(self.batch, location)
        self.assert_response(
            response,
            next_state="confirm_unload_all",
            data=data,
        )

    def test_set_destination_all_with_confirmation(self):
        """Endpoint called with a barcode for another (valid) location, confirm"""
        move_lines = self.move_lines
        self._set_dest_package_and_done(move_lines, self.bin1)
        move_lines.write({"location_dest_id": self.packing_a_location.id})

        response = self.service.dispatch(
            "set_destination_all",
            params={
                "picking_batch_id": self.batch.id,
                "barcode": self.packing_b_location.barcode,
                "confirmation": True,
            },
        )
        self.assertRecordValues(
            move_lines,
            [
                {"location_dest_id": self.packing_b_location.id},
                {"location_dest_id": self.packing_b_location.id},
                {"location_dest_id": self.packing_b_location.id},
            ],
        )
        self.assert_response(
            response,
            next_state="start",
            message={"message_type": "success", "body": "Batch Transfer complete"},
        )


class ClusterPickingUnloadSplitCase(ClusterPickingUnloadingCommonCase):
    """Tests covering the /unload_split endpoint

    All the destinations of the bins were the same so the "unload all" screen
    was presented to the user, but they want different destination, so they hit
    the "split" button. From now on, the workflow should use the "unload single"
    screen even if the destinations are the same.
    """

    def test_unload_split_ok(self):
        """Call /unload_split and continue to unload single"""
        move_lines = self.move_lines
        # put destination packages, the whole quantity on lines and a similar
        # destination (when /set_destination_all is called, all the lines to
        # unload must have the same destination)
        self._set_dest_package_and_done(move_lines, self.bin1)
        move_lines.write({"location_dest_id": self.packing_location.id})

        response = self.service.dispatch(
            "unload_split", params={"picking_batch_id": self.batch.id}
        )
        location = move_lines[0].location_dest_id
        data = self._data_for_batch(self.batch, location, pack=self.bin1)
        self.assert_response(
            # the remaining move line still needs to be picked
            response,
            next_state="unload_single",
            data=data,
        )


class ClusterPickingUnloadScanPackCase(ClusterPickingUnloadingCommonCase):
    """Tests covering the /unload_scan_pack endpoint

    Goods have been put in the package bins, they have different destinations
    or /unload_split has been called, now user has to unload package per
    package. For this, they'll first scan the bin package, which will call the
    endpoint /unload_scan_pack. (second step will be to set the destination
    with /unload_scan_destination, in a different test case)
    """

    @classmethod
    def setUpClassBaseData(cls, *args, **kwargs):
        super().setUpClassBaseData(*args, **kwargs)
        cls._set_dest_package_and_done(cls.move_lines, cls.bin1)
        cls.move_lines[:2].write({"location_dest_id": cls.packing_a_location.id})
        cls.move_lines[2:].write({"location_dest_id": cls.packing_b_location.id})

    def test_unload_scan_pack_ok(self):
        """Endpoint /unload_scan_pack is called, result ok"""
        response = self.service.dispatch(
            "unload_scan_pack",
            params={
                "picking_batch_id": self.batch.id,
                "package_id": self.bin1.id,
                "barcode": self.bin1.name,
            },
        )
        location = self.move_lines[0].location_dest_id
        data = self._data_for_batch(self.batch, location, pack=self.bin1)
        self.assert_response(
            response,
            next_state="unload_set_destination",
            data=data,
        )

    def test_unload_scan_pack_wrong_barcode(self):
        """Endpoint /unload_scan_pack is called, wrong barcode scanned"""
        response = self.service.dispatch(
            "unload_scan_pack",
            params={
                "picking_batch_id": self.batch.id,
                "package_id": self.bin1.id,
                "barcode": self.bin2.name,
            },
        )
        location = self.move_lines[0].location_dest_id
        data = self._data_for_batch(self.batch, location, pack=self.bin1)
        self.assert_response(
            response,
            next_state="unload_single",
            data=data,
            message={"message_type": "error", "body": "Wrong bin"},
        )


class ClusterPickingUnloadScanDestinationCase(ClusterPickingUnloadingCommonCase):
    """Tests covering the /unload_scan_destination endpoint

    Goods have been put in the package bins, they have different destinations
    or /unload_split has been called, now user has to unload package per
    package. For this, they'll first scanned the bin package already (endpoint
    /unload_scan_pack), now they have to set the destination with
    /unload_scan_destination for the scanned pack.
    """

    @classmethod
    def setUpClassBaseData(cls, *args, **kwargs):
        super().setUpClassBaseData(*args, **kwargs)
        cls.bin1_lines = cls.move_lines[:1]
        cls.bin2_lines = cls.move_lines[1:]
        cls._set_dest_package_and_done(cls.bin1_lines, cls.bin1)
        cls._set_dest_package_and_done(cls.bin2_lines, cls.bin2)
        cls.bin1_lines.write({"location_dest_id": cls.packing_a_location.id})
        cls.bin2_lines.write({"location_dest_id": cls.packing_b_location.id})
        cls.one_line_picking = cls.batch.picking_ids.filtered(
            lambda picking: len(picking.move_lines) == 1
        )
        cls.two_lines_picking = cls.batch.picking_ids.filtered(
            lambda picking: len(picking.move_lines) == 2
        )

    def test_unload_scan_destination_ok(self):
        """Endpoint /unload_scan_destination is called, result ok"""
        dest_location = self.bin1_lines[0].location_dest_id

        response = self.service.dispatch(
            "unload_scan_destination",
            params={
                "picking_batch_id": self.batch.id,
                "package_id": self.bin1.id,
                "barcode": dest_location.barcode,
            },
        )

        # The scan of destination set 'unloaded' to True to track the fact
        # that we set the destination for the line. In this case, the line
        # and the stock.picking are 'done' because all the lines of the picking
        # have been unloaded
        self.assertRecordValues(self.one_line_picking, [{"state": "done"}])
        self.assertRecordValues(self.two_lines_picking, [{"state": "assigned"}])
        self.assertRecordValues(
            self.bin1_lines,
            [
                {
                    "shopfloor_unloaded": True,
                    "qty_done": 10,
                    "state": "done",
                    "picking_id": self.one_line_picking.id,
                    "location_dest_id": self.packing_a_location.id,
                }
            ],
        )
        self.assertRecordValues(
            self.bin2_lines,
            [
                {
                    "shopfloor_unloaded": False,
                    "qty_done": 10,
                    "state": "assigned",
                    "picking_id": self.two_lines_picking.id,
                    "location_dest_id": self.packing_b_location.id,
                },
                {
                    "shopfloor_unloaded": False,
                    "qty_done": 10,
                    "state": "assigned",
                    "picking_id": self.two_lines_picking.id,
                    "location_dest_id": self.packing_b_location.id,
                },
            ],
        )
        self.assertRecordValues(self.batch, [{"state": "in_progress"}])

        location = self.bin2_lines[0].location_dest_id
        data = self._data_for_batch(self.batch, location, pack=self.bin2)
        self.assert_response(
            response,
            next_state="unload_single",
            data=data,
        )

    def test_unload_scan_destination_one_line_of_picking_only(self):
        """Endpoint /unload_scan_destination is called, only one line of picking"""
        # For this test, we assume the move in bin1 is already done.
        self.one_line_picking._action_done()
        # And for the second picking, we put one line bin2 and one line in bin3
        # so the user would have to go through 2 screens for each pack.
        # After scanning and setting the destination for bin2, the picking will
        # still be "assigned" and they'll have to scan bin3 (but this test stops
        # at bin2)
        bin3 = self.env["stock.quant.package"].create({})
        bin2_line = self.bin2_lines[0]
        bin3_line = self.bin2_lines[1]
        self._set_dest_package_and_done(bin3_line, bin3)

        dest_location = bin2_line.location_dest_id

        response = self.service.dispatch(
            "unload_scan_destination",
            params={
                "picking_batch_id": self.batch.id,
                "package_id": self.bin2.id,
                "barcode": dest_location.barcode,
            },
        )

        # The scan of destination set 'unloaded' to True to track the fact
        # that we set the destination for the line. The picking is still
        # assigned because the second line still has to be unloaded.
        self.assertRecordValues(self.two_lines_picking, [{"state": "assigned"}])
        self.assertRecordValues(
            bin2_line,
            [
                {
                    "shopfloor_unloaded": True,
                    "qty_done": 10,
                    "state": "assigned",
                    "picking_id": self.two_lines_picking.id,
                    "location_dest_id": self.packing_b_location.id,
                }
            ],
        )
        self.assertRecordValues(
            bin3_line,
            [
                {
                    "shopfloor_unloaded": False,
                    "qty_done": 10,
                    "state": "assigned",
                    "picking_id": self.two_lines_picking.id,
                    "location_dest_id": self.packing_b_location.id,
                }
            ],
        )
        self.assertRecordValues(self.batch, [{"state": "in_progress"}])
        location = bin3_line.location_dest_id
        data = self._data_for_batch(self.batch, location, pack=bin3)
        self.assert_response(
            response,
            next_state="unload_single",
            data=data,
        )

    def test_unload_scan_destination_last_line(self):
        """Endpoint /unload_scan_destination is called on last line"""
        # For this test, we assume the move in bin1 is already done.
        self.one_line_picking._action_done()
        # And for the second picking, bin2 was already unloaded,
        # remains bin3 to unload.
        bin3 = self.env["stock.quant.package"].create({})
        bin2_line = self.bin2_lines[0]
        bin3_line = self.bin2_lines[1]
        self._set_dest_package_and_done(bin3_line, bin3)
        bin2_line.shopfloor_unloaded = True

        dest_location = bin3_line.location_dest_id

        response = self.service.dispatch(
            "unload_scan_destination",
            params={
                "picking_batch_id": self.batch.id,
                "package_id": bin3.id,
                "barcode": dest_location.barcode,
            },
        )

        # The scan of destination set 'unloaded' to True to track the fact
        # that we set the destination for the line. The picking is done
        # because all the lines have been unloaded
        self.assertRecordValues(self.two_lines_picking, [{"state": "done"}])
        self.assertRecordValues(
            bin3_line,
            [
                {
                    "shopfloor_unloaded": True,
                    "qty_done": 10,
                    "state": "done",
                    "picking_id": self.two_lines_picking.id,
                    "location_dest_id": self.packing_b_location.id,
                }
            ],
        )
        self.assertRecordValues(self.batch, [{"state": "done"}])

        self.assert_response(
            response,
            next_state="start",
            message={"body": "Batch Transfer complete", "message_type": "success"},
        )

    def test_unload_scan_destination_error_location_not_found(self):
        """Endpoint called with a barcode not existing for a location"""
        response = self.service.dispatch(
            "unload_scan_destination",
            params={
                "picking_batch_id": self.batch.id,
                "package_id": self.bin1.id,
                "barcode": "¤",
            },
        )
        location = self.bin1_lines[0].location_dest_id
        data = self._data_for_batch(self.batch, location, pack=self.bin1)
        self.assert_response(
            response,
            next_state="unload_set_destination",
            data=data,
            message={
                "message_type": "error",
                "body": "No location found for this barcode.",
            },
        )

    def test_unload_scan_destination_error_location_invalid(self):
        """Endpoint called with a barcode for an invalid location

        It is invalid when the location is not the destination location or
        sublocation of the picking type.
        """
        response = self.service.dispatch(
            "unload_scan_destination",
            params={
                "picking_batch_id": self.batch.id,
                "package_id": self.bin1.id,
                "barcode": self.dispatch_location.barcode,
            },
        )
        location = self.bin1_lines[0].location_dest_id
        data = self._data_for_batch(self.batch, location, pack=self.bin1)
        self.assert_response(
            response,
            next_state="unload_set_destination",
            data=data,
            message={"message_type": "error", "body": "You cannot place it here"},
        )

    def test_unload_scan_destination_error_location_move_invalid(self):
        """Endpoint called with a barcode for an invalid location

        It is invalid when the location is not a sublocation of the picking
        or move destination
        """
        self.bin1_lines[0].picking_id.location_dest_id = self.packing_a_location
        response = self.service.dispatch(
            "unload_scan_destination",
            params={
                "picking_batch_id": self.batch.id,
                "package_id": self.bin1.id,
                "barcode": self.packing_b_location.barcode,
            },
        )
        location = self.bin1_lines[0].location_dest_id
        data = self._data_for_batch(self.batch, location, pack=self.bin1)
        self.assert_response(
            response,
            next_state="unload_set_destination",
            data=data,
            message=self.service.msg_store.dest_location_not_allowed(),
        )

    def test_unload_scan_destination_need_confirmation(self):
        """Endpoint called with a barcode for another (valid) location"""
        response = self.service.dispatch(
            "unload_scan_destination",
            params={
                "picking_batch_id": self.batch.id,
                "package_id": self.bin1.id,
                "barcode": self.packing_b_location.barcode,
            },
        )
        location = self.bin1_lines[0].location_dest_id
        data = self._data_for_batch(self.batch, location, pack=self.bin1)
        self.assert_response(
            response,
            next_state="confirm_unload_set_destination",
            data=data,
        )

    def test_unload_scan_destination_with_confirmation(self):
        """Endpoint called with a barcode for another (valid) location, confirm"""
        response = self.service.dispatch(
            "unload_scan_destination",
            params={
                "picking_batch_id": self.batch.id,
                "package_id": self.bin2.id,
                "barcode": self.packing_a_location.barcode,
                "confirmation": True,
            },
        )
        self.assertRecordValues(
            self.bin2.quant_ids,
            [
                {"location_id": self.packing_a_location.id},
                {"location_id": self.packing_a_location.id},
            ],
        )
        self.assertRecordValues(
            self.two_lines_picking.move_line_ids,
            [
                {"location_dest_id": self.packing_a_location.id},
                {"location_dest_id": self.packing_a_location.id},
            ],
        )
        self.assert_response(response, next_state="unload_single", data=self.ANY)

    def test_unload_scan_destination_completion_info(self):
        """/unload_scan_destination that make chained picking ready"""
        picking = self.one_line_picking
        dest_location = picking.move_line_ids.location_dest_id
        self.picking_type.sudo().display_completion_info = True

        # create a chained picking after the current one
        next_picking = picking.copy(
            {
                "picking_type_id": self.wh.out_type_id.id,
                "location_id": picking.location_dest_id.id,
                "location_dest_id": self.customer_location.id,
            }
        )
        next_picking.move_lines.write(
            {"move_orig_ids": [(6, 0, picking.move_lines.ids)]}
        )
        next_picking.action_confirm()

        response = self.service.dispatch(
            "unload_scan_destination",
            params={
                "picking_batch_id": self.batch.id,
                "package_id": self.bin1.id,
                "barcode": dest_location.barcode,
            },
        )
        location = self.bin2_lines[0].location_dest_id
        data = self._data_for_batch(self.batch, location, pack=self.bin2)
        self.assert_response(
            response,
            next_state="unload_single",
            popup={
                "body": "Last operation of transfer {}. Next operation "
                "({}) is ready to proceed.".format(picking.name, next_picking.name)
            },
            data=data,
        )
