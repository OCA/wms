from unittest import mock

from .test_zone_picking_base import ZonePickingCommonCase


class ZonePickingUnloadSetDestinationCase(ZonePickingCommonCase):
    """Tests for endpoint used from unload_set_destination

    * /unload_set_destination

    """

    def test_unload_set_destination_wrong_parameters(self):
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        move_line = self.picking1.move_line_ids
        package = move_line.package_id
        response = self.service.dispatch(
            "unload_set_destination",
            params={
                "zone_location_id": 1234567890,
                "picking_type_id": picking_type.id,
                "package_id": package.id,
                "barcode": "BARCODE",
            },
        )
        self.assert_response_start(
            response, message=self.service.msg_store.record_not_found(),
        )
        response = self.service.dispatch(
            "unload_set_destination",
            params={
                "zone_location_id": zone_location.id,
                "picking_type_id": 1234567890,
                "package_id": package.id,
                "barcode": "BARCODE",
            },
        )
        self.assert_response_start(
            response, message=self.service.msg_store.record_not_found(),
        )
        response = self.service.dispatch(
            "unload_set_destination",
            params={
                "zone_location_id": zone_location.id,
                "picking_type_id": picking_type.id,
                "package_id": 1234567890,
                "barcode": "BARCODE",
            },
        )
        move_lines = self.service._find_location_move_lines(zone_location, picking_type)
        self.assert_response_select_line(
            response,
            zone_location,
            picking_type,
            move_lines,
            message=self.service.msg_store.record_not_found(),
        )

    def test_unload_set_destination_no_location_found(self):
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        move_line = self.picking1.move_line_ids
        # set the destination package
        self.service._set_destination_package(
            zone_location,
            picking_type,
            move_line,
            move_line.product_uom_qty,
            self.free_package,
        )
        response = self.service.dispatch(
            "unload_set_destination",
            params={
                "zone_location_id": zone_location.id,
                "picking_type_id": picking_type.id,
                "package_id": self.free_package.id,
                "barcode": "UNKNOWN",
            },
        )
        self.assert_response_unload_set_destination(
            response,
            zone_location,
            picking_type,
            move_line,
            message=self.service.msg_store.no_location_found(),
        )

    def test_unload_set_destination_location_not_allowed(self):
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        move_line = self.picking1.move_line_ids
        # set the destination package
        self.service._set_destination_package(
            zone_location,
            picking_type,
            move_line,
            move_line.product_uom_qty,
            self.free_package,
        )
        response = self.service.dispatch(
            "unload_set_destination",
            params={
                "zone_location_id": zone_location.id,
                "picking_type_id": picking_type.id,
                "package_id": self.free_package.id,
                "barcode": self.customer_location.barcode,
            },
        )
        self.assert_response_unload_set_destination(
            response,
            zone_location,
            picking_type,
            move_line,
            message=self.service.msg_store.dest_location_not_allowed(),
        )

    def test_unload_set_destination_confirm_location(self):
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        move_line = self.picking1.move_line_ids
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
        # set the destination package
        self.service._set_destination_package(
            zone_location,
            picking_type,
            move_line,
            move_line.product_uom_qty,
            self.free_package,
        )
        response = self.service.dispatch(
            "unload_set_destination",
            params={
                "zone_location_id": zone_location.id,
                "picking_type_id": picking_type.id,
                "package_id": self.free_package.id,
                "barcode": packing_sublocation.barcode,
            },
        )
        self.assert_response_unload_set_destination(
            response,
            zone_location,
            picking_type,
            move_line,
            message=self.service.msg_store.confirm_location_changed(
                picking_type.default_location_dest_id, packing_sublocation
            ),
            confirmation_required=True,
        )

    def test_unload_set_destination_ok_buffer_empty(self):
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        move_line = self.picking1.move_line_ids
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
        # set the destination package
        self.service._set_destination_package(
            zone_location,
            picking_type,
            move_line,
            move_line.product_uom_qty,
            self.free_package,
        )
        with mock.patch.object(
            type(self.picking1), "_send_confirmation_email"
        ) as send_confirmation_email:
            response = self.service.dispatch(
                "unload_set_destination",
                params={
                    "zone_location_id": zone_location.id,
                    "picking_type_id": picking_type.id,
                    "package_id": self.free_package.id,
                    "barcode": packing_sublocation.barcode,
                    "confirmation": True,
                },
            )
            send_confirmation_email.assert_called_once()
        # check data
        self.assertEqual(move_line.location_dest_id, packing_sublocation)
        self.assertEqual(move_line.move_id.state, "done")
        # check response
        move_lines = self.service._find_location_move_lines(zone_location, picking_type)
        self.assert_response_select_line(
            response,
            zone_location,
            picking_type,
            move_lines,
            message=self.service.msg_store.buffer_complete(),
        )

    def test_unload_set_destination_ok_buffer_not_empty(self):
        zone_location = self.zone_location
        picking_type = self.picking5.picking_type_id
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
        # process 1/2 buffer line
        with mock.patch.object(
            type(self.picking5), "_send_confirmation_email"
        ) as send_confirmation_email:
            response = self.service.dispatch(
                "unload_set_destination",
                params={
                    "zone_location_id": zone_location.id,
                    "picking_type_id": picking_type.id,
                    "package_id": self.free_package.id,
                    "barcode": self.packing_location.barcode,
                },
            )
            send_confirmation_email.assert_not_called()
        # check data
        move_line = self.picking5.move_line_ids.filtered(
            lambda l: l.result_package_id == self.free_package
        )
        self.assertEqual(move_line.location_dest_id, self.packing_location)
        self.assertEqual(move_line.move_id.state, "done")
        # check response
        buffer_line = self.service._find_buffer_move_lines(zone_location, picking_type)
        completion_info = self.service.actions_for("completion.info")
        completion_info_popup = completion_info.popup(buffer_line)
        self.assert_response_unload_single(
            response,
            zone_location,
            picking_type,
            buffer_line,
            popup=completion_info_popup,
        )
