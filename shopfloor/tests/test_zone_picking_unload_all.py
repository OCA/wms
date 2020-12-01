from .test_zone_picking_base import ZonePickingCommonCase


class ZonePickingUnloadAllCase(ZonePickingCommonCase):
    """Tests for endpoint used from unload_all

    * /set_destination_all
    * /unload_split

    """

    def test_set_destination_all_wrong_parameters(self):
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        response = self.service.dispatch(
            "set_destination_all",
            params={
                "zone_location_id": 1234567890,
                "picking_type_id": picking_type.id,
                "barcode": "UNKNOWN",
            },
        )
        self.assert_response_start(
            response, message=self.service.msg_store.record_not_found(),
        )
        response = self.service.dispatch(
            "set_destination_all",
            params={
                "zone_location_id": zone_location.id,
                "picking_type_id": 1234567890,
                "barcode": "UNKNOWN",
            },
        )
        self.assert_response_start(
            response, message=self.service.msg_store.record_not_found(),
        )

    def test_set_destination_all_different_destination(self):
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        move_line1 = self.picking5.move_line_ids[0]
        move_line2 = self.picking5.move_line_ids[1]
        another_package = self.env["stock.quant.package"].create(
            {"name": "ANOTHER_PACKAGE"}
        )
        # change the destination location of one move line
        move_line2.location_dest_id = self.zone_sublocation3
        # set the destination package on lines
        self.service._set_destination_package(
            zone_location,
            picking_type,
            move_line1,
            move_line1.product_uom_qty,
            self.free_package,
        )
        self.service._set_destination_package(
            zone_location,
            picking_type,
            move_line2,
            move_line2.product_uom_qty,
            another_package,
        )
        # set destination location for all lines in the buffer
        response = self.service.dispatch(
            "set_destination_all",
            params={
                "zone_location_id": zone_location.id,
                "picking_type_id": picking_type.id,
                "barcode": self.packing_location.barcode,
            },
        )
        # check response
        buffer_lines = self.service._find_buffer_move_lines(zone_location, picking_type)
        self.assert_response_unload_all(
            response,
            zone_location,
            picking_type,
            buffer_lines,
            message=self.service.msg_store.lines_different_dest_location(),
        )

    def test_set_destination_all_confirm_destination(self):
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        move_line1 = self.picking5.move_line_ids[0]
        move_line2 = self.picking5.move_line_ids[1]
        another_package = self.env["stock.quant.package"].create(
            {"name": "ANOTHER_PACKAGE"}
        )
        packing_sublocation = (
            self.env["stock.location"]
            .sudo()
            .create(
                {
                    "name": "Packing sublocation",
                    "location_id": self.packing_location.id,
                    "barcode": "PACKING_SUBLOCATION",
                }
            )
        )
        # set the destination package on lines
        self.service._set_destination_package(
            zone_location,
            picking_type,
            move_line1,
            move_line1.product_uom_qty,
            self.free_package,
        )
        self.service._set_destination_package(
            zone_location,
            picking_type,
            move_line2,
            move_line2.product_uom_qty,
            another_package,
        )
        # set destination location for all lines in the buffer
        response = self.service.dispatch(
            "set_destination_all",
            params={
                "zone_location_id": zone_location.id,
                "picking_type_id": picking_type.id,
                "barcode": packing_sublocation.barcode,
            },
        )
        # check response
        buffer_lines = self.service._find_buffer_move_lines(zone_location, picking_type)
        self.assert_response_unload_all(
            response,
            zone_location,
            picking_type,
            buffer_lines,
            message=self.service.msg_store.confirm_location_changed(
                picking_type.default_location_dest_id, packing_sublocation,
            ),
            confirmation_required=True,
        )

    def test_set_destination_all_ok(self):
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        move_line1 = self.picking5.move_line_ids[0]
        move_line2 = self.picking5.move_line_ids[1]
        another_package = self.env["stock.quant.package"].create(
            {"name": "ANOTHER_PACKAGE"}
        )
        # set the destination package on lines
        self.service._set_destination_package(
            zone_location,
            picking_type,
            move_line1,
            move_line1.product_uom_qty,
            self.free_package,
        )
        self.service._set_destination_package(
            zone_location,
            picking_type,
            move_line2,
            move_line2.product_uom_qty,
            another_package,
        )
        # set destination location for all lines in the buffer
        response = self.service.dispatch(
            "set_destination_all",
            params={
                "zone_location_id": zone_location.id,
                "picking_type_id": picking_type.id,
                "barcode": self.packing_location.barcode,
            },
        )
        # check data
        self.assertEqual(self.picking5.state, "done")
        # buffer should be empty
        buffer_lines = self.service._find_buffer_move_lines(zone_location, picking_type)
        self.assertFalse(buffer_lines)
        # check response
        move_lines = self.service._find_location_move_lines(zone_location, picking_type)
        self.assert_response_select_line(
            response,
            zone_location,
            picking_type,
            move_lines,
            message=self.service.msg_store.buffer_complete(),
        )

    def test_set_destination_all_location_not_allowed(self):
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        move_line = self.picking1.move_line_ids
        # set the destination package on lines
        self.service._set_destination_package(
            zone_location,
            picking_type,
            move_line,
            move_line.product_uom_qty,
            self.free_package,
        )
        response = self.service.dispatch(
            "set_destination_all",
            params={
                "zone_location_id": zone_location.id,
                "picking_type_id": picking_type.id,
                "barcode": self.customer_location.barcode,
            },
        )
        # check response
        buffer_lines = self.service._find_buffer_move_lines(zone_location, picking_type)
        self.assert_response_unload_all(
            response,
            zone_location,
            picking_type,
            buffer_lines,
            message=self.service.msg_store.location_not_allowed(),
        )

    def test_set_destination_all_location_not_found(self):
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        move_line = self.picking1.move_line_ids
        # set the destination package on lines
        self.service._set_destination_package(
            zone_location,
            picking_type,
            move_line,
            move_line.product_uom_qty,
            self.free_package,
        )
        response = self.service.dispatch(
            "set_destination_all",
            params={
                "zone_location_id": zone_location.id,
                "picking_type_id": picking_type.id,
                "barcode": "UNKNOWN",
            },
        )
        # check response
        buffer_lines = self.service._find_buffer_move_lines(zone_location, picking_type)
        self.assert_response_unload_all(
            response,
            zone_location,
            picking_type,
            buffer_lines,
            message=self.service.msg_store.no_location_found(),
        )

    def test_unload_split_buffer_empty(self):
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        response = self.service.dispatch(
            "unload_split",
            params={
                "zone_location_id": zone_location.id,
                "picking_type_id": picking_type.id,
            },
        )
        # check response
        move_lines = self.service._find_location_move_lines(zone_location, picking_type)
        self.assert_response_select_line(
            response,
            zone_location,
            picking_type,
            move_lines,
            message=self.service.msg_store.buffer_complete(),
        )

    def test_unload_split_buffer_one_line(self):
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        move_line = self.picking1.move_line_ids
        # put one line in the buffer
        self.service._set_destination_package(
            zone_location,
            picking_type,
            move_line,
            move_line.product_uom_qty,
            self.free_package,
        )
        response = self.service.dispatch(
            "unload_split",
            params={
                "zone_location_id": zone_location.id,
                "picking_type_id": picking_type.id,
            },
        )
        # check response
        buffer_lines = self.service._find_buffer_move_lines(zone_location, picking_type)
        self.assert_response_unload_set_destination(
            response, zone_location, picking_type, buffer_lines,
        )

    def test_unload_split_buffer_multi_lines(self):
        zone_location = self.zone_location
        picking_type = self.picking5.picking_type_id
        move_line = self.picking5.move_line_ids
        # put several lines in the buffer
        self.another_package = self.env["stock.quant.package"].create(
            {"name": "ANOTHER_PACKAGE"}
        )
        for move_line, package_dest in zip(
            self.picking5.move_line_ids, self.free_package | self.another_package
        ):
            self.service._set_destination_package(
                zone_location,
                picking_type,
                move_line,
                move_line.product_uom_qty,
                package_dest,
            )
        response = self.service.dispatch(
            "unload_split",
            params={
                "zone_location_id": zone_location.id,
                "picking_type_id": picking_type.id,
            },
        )
        # check response
        buffer_lines = self.service._find_buffer_move_lines(zone_location, picking_type)
        self.assert_response_unload_single(
            response, zone_location, picking_type, buffer_lines[0],
        )
