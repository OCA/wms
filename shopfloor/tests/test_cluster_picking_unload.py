from .test_cluster_picking_base import ClusterPickingCommonCase


class ClusterPickingUnloadingCommonCase(ClusterPickingCommonCase):
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
        cls._simulate_batch_selected(cls.batch)
        cls.bin1 = cls.env["stock.quant.package"].create({})
        cls.bin2 = cls.env["stock.quant.package"].create({})
        cls.packing_a_location = cls.env["stock.location"].create(
            {
                "name": "Packing A",
                "barcode": "Packing-A",
                "location_id": cls.packing_location.id,
            }
        )
        cls.packing_b_location = cls.env["stock.location"].create(
            {
                "name": "Packing B",
                "barcode": "Packing-B",
                "location_id": cls.packing_location.id,
            }
        )

    @classmethod
    def _set_dest_package_and_done(cls, move_lines, dest_package):
        """Simulate what would have been done in the previous steps"""
        for line in move_lines:
            line.write(
                {"qty_done": line.product_uom_qty, "result_package_id": dest_package.id}
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
        move_lines = self.batch.mapped("picking_ids.move_line_ids")
        self._set_dest_package_and_done(move_lines[:2], self.bin1)
        self._set_dest_package_and_done(move_lines[2:], self.bin2)
        move_lines.write({"location_dest_id": self.packing_location.id})
        response = self.service.dispatch(
            "prepare_unload", params={"picking_batch_id": self.batch.id}
        )
        self.assertRecordValues(self.batch, [{"cluster_picking_unload_all": True}])
        self.assert_response(
            response,
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

    def test_prepare_unload_different_dest(self):
        """All move lines have different destination locations"""
        move_lines = self.batch.mapped("picking_ids.move_line_ids")
        self._set_dest_package_and_done(move_lines[:2], self.bin1)
        self._set_dest_package_and_done(move_lines[2:], self.bin2)
        move_lines[:1].write({"location_dest_id": self.packing_a_location.id})
        move_lines[:1].write({"location_dest_id": self.packing_b_location.id})
        response = self.service.dispatch(
            "prepare_unload", params={"picking_batch_id": self.batch.id}
        )
        self.assertRecordValues(self.batch, [{"cluster_picking_unload_all": False}])
        first_line = move_lines[0]
        self.assert_response(
            response,
            next_state="unload_single",
            data={
                "id": self.batch.id,
                "name": self.batch.name,
                "package": {"id": self.bin1.id, "name": self.bin1.name},
                "location_dst": {
                    "id": first_line.location_dest_id.id,
                    "name": first_line.location_dest_id.name,
                },
            },
        )


class ClusterPickingSetDestinationAllCase(ClusterPickingUnloadingCommonCase):
    """Tests covering the /set_destination_all endpoint

    All the picked lines go to the same destination, a single call to this
    endpoint set them as "unloaded" and set the destination. When the last
    available line of a picking is unloaded, the picking is set to 'done'.
    """

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)
        # this is what the /prepare_endpoint method would have set as all the
        # destinations are the same:
        cls.batch.cluster_picking_unload_all = True

    def test_set_destination_all_ok(self):
        """Set destination on all lines for the full batch and end the process"""
        move_lines = self.batch.mapped("picking_ids.move_line_ids")
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
            message={"message_type": "success", "message": "Batch Transfer complete"},
        )

    def test_set_destination_all_remaining_lines(self):
        """Set destination on all lines for a part of the batch"""
        move_lines = self.batch.mapped("picking_ids.move_line_ids")
        # Put destination packages, the whole quantity on lines and a similar
        # destination (when /set_destination_all is called, all the lines to
        # unload must have the same destination).
        # However, we keep a line without qty_done and destination package,
        # so when the dest location is set, the endpoint should route back
        # to the 'start_line' state to work on the remaining line.
        lines_to_unload = move_lines[:2]
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
        one_line_picking = self.batch.picking_ids[0]
        two_lines_picking = self.batch.picking_ids[1]
        self.assertRecordValues(one_line_picking, [{"state": "done"}])
        self.assertRecordValues(two_lines_picking, [{"state": "assigned"}])
        self.assertRecordValues(
            move_lines,
            [
                {
                    "shopfloor_unloaded": True,
                    "qty_done": 10,
                    "state": "done",
                    "picking_id": one_line_picking.id,
                    "location_dest_id": self.packing_location.id,
                },
                {
                    "shopfloor_unloaded": True,
                    "qty_done": 10,
                    # will be done when the second line of the picking is unloaded
                    "state": "assigned",
                    "picking_id": two_lines_picking.id,
                    "location_dest_id": self.packing_location.id,
                },
                {
                    "shopfloor_unloaded": False,
                    "qty_done": 0,
                    "state": "assigned",
                    "picking_id": two_lines_picking.id,
                    "location_dest_id": self.packing_location.id,
                },
            ],
        )
        self.assertRecordValues(self.batch, [{"state": "in_progress"}])

        self.assert_response(
            # the remaining move line still needs to be picked
            response,
            next_state="start_line",
            data=self._line_data(move_lines[2]),
        )

    def test_set_destination_all_but_different_dest(self):
        """Endpoint was called but destinations are different"""
        move_lines = self.batch.mapped("picking_ids.move_line_ids")
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
        self.assertRecordValues(self.batch, [{"cluster_picking_unload_all": False}])
        self.assert_response(
            response,
            next_state="unload_single",
            data={
                "id": self.batch.id,
                "name": self.batch.name,
                "package": {"id": self.bin1.id, "name": self.bin1.name},
                "location_dst": {
                    "id": move_lines[0].location_dest_id.id,
                    "name": move_lines[0].location_dest_id.name,
                },
            },
        )

    def test_set_destination_all_error_location_not_found(self):
        """Endpoint called with a barcode not existing for a location"""
        move_lines = self.batch.mapped("picking_ids.move_line_ids")
        self._set_dest_package_and_done(move_lines, self.bin1)
        move_lines.write({"location_dest_id": self.packing_a_location.id})

        response = self.service.dispatch(
            "set_destination_all",
            params={"picking_batch_id": self.batch.id, "barcode": "NOTFOUND"},
        )
        self.assert_response(
            response,
            next_state="unload_all",
            data={
                "id": self.batch.id,
                "name": self.batch.name,
                "location_dst": {
                    "id": move_lines[0].location_dest_id.id,
                    "name": move_lines[0].location_dest_id.name,
                },
            },
            message={
                "message_type": "error",
                "message": "No location found for this barcode.",
            },
        )

    def test_set_destination_all_error_location_invalid(self):
        """Endpoint called with a barcode for an invalid location

        It is invalid when the location is not the destination location or
        sublocation of the picking type.
        """
        move_lines = self.batch.mapped("picking_ids.move_line_ids")
        self._set_dest_package_and_done(move_lines, self.bin1)
        move_lines.write({"location_dest_id": self.packing_a_location.id})

        response = self.service.dispatch(
            "set_destination_all",
            params={
                "picking_batch_id": self.batch.id,
                "barcode": self.dispatch_location.barcode,
            },
        )
        self.assert_response(
            response,
            next_state="unload_all",
            data={
                "id": self.batch.id,
                "name": self.batch.name,
                "location_dst": {
                    "id": move_lines[0].location_dest_id.id,
                    "name": move_lines[0].location_dest_id.name,
                },
            },
            message={"message_type": "error", "message": "You cannot place it here"},
        )

    def test_set_destination_all_need_confirmation(self):
        """Endpoint called with a barcode for another (valid) location"""
        move_lines = self.batch.mapped("picking_ids.move_line_ids")
        self._set_dest_package_and_done(move_lines, self.bin1)
        move_lines.write({"location_dest_id": self.packing_a_location.id})

        response = self.service.dispatch(
            "set_destination_all",
            params={
                "picking_batch_id": self.batch.id,
                "barcode": self.packing_b_location.barcode,
            },
        )
        self.assert_response(
            response,
            next_state="confirm_unload_all",
            data={
                "id": self.batch.id,
                "name": self.batch.name,
                "location_dst": {
                    "id": move_lines[0].location_dest_id.id,
                    "name": move_lines[0].location_dest_id.name,
                },
            },
        )

    def test_set_destination_all_with_confirmation(self):
        """Endpoint called with a barcode for another (valid) location, confirm"""
        move_lines = self.batch.mapped("picking_ids.move_line_ids")
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
            message={"message_type": "success", "message": "Batch Transfer complete"},
        )


class ClusterPickingUnloadSplitCase(ClusterPickingUnloadingCommonCase):
    """Tests covering the /unload_split endpoint

    All the destinations of the bins were the same so the "unload all" screen
    was presented to the user, but they want different destination, so they hit
    the "split" button. From now on, the workflow should use the "unload single"
    screen even if the destinations are the same.
    """

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)
        # this is what the /prepare_endpoint method would have set as all the
        # destinations are the same:
        cls.batch.cluster_picking_unload_all = True

    def test_unload_split_ok(self):
        """Call /unload_split and continue to unload single"""
        move_lines = self.batch.mapped("picking_ids.move_line_ids")
        # put destination packages, the whole quantity on lines and a similar
        # destination (when /set_destination_all is called, all the lines to
        # unload must have the same destination)
        self._set_dest_package_and_done(move_lines, self.bin1)
        move_lines.write({"location_dest_id": self.packing_location.id})

        response = self.service.dispatch(
            "unload_split", params={"picking_batch_id": self.batch.id}
        )
        self.assertRecordValues(self.batch, [{"cluster_picking_unload_all": False}])
        self.assert_response(
            # the remaining move line still needs to be picked
            response,
            next_state="unload_single",
            data={
                "id": self.batch.id,
                "name": self.batch.name,
                "package": {"id": self.bin1.id, "name": self.bin1.name},
                "location_dst": {
                    "id": move_lines[0].location_dest_id.id,
                    "name": move_lines[0].location_dest_id.name,
                },
            },
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
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)
        cls.batch.cluster_picking_unload_all = False
        cls.move_lines = cls.batch.mapped("picking_ids.move_line_ids")
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
        self.assert_response(
            response,
            next_state="unload_set_destination",
            data={
                "id": self.batch.id,
                "name": self.batch.name,
                "package": {"id": self.bin1.id, "name": self.bin1.name},
                "location_dst": {
                    "id": self.move_lines[0].location_dest_id.id,
                    "name": self.move_lines[0].location_dest_id.name,
                },
            },
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
        self.assert_response(
            response,
            next_state="unload_single",
            data={
                "id": self.batch.id,
                "name": self.batch.name,
                "package": {"id": self.bin1.id, "name": self.bin1.name},
                "location_dst": {
                    "id": self.move_lines[0].location_dest_id.id,
                    "name": self.move_lines[0].location_dest_id.name,
                },
            },
            message={"message_type": "error", "message": "Wrong bin"},
        )
