# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from .test_zone_picking_base import ZonePickingCommonCase

# pylint: disable=missing-return


class ZonePickingUnloadSetDestinationCase(ZonePickingCommonCase):
    """Tests for endpoint used from unload_set_destination

    * /unload_set_destination

    """

    @classmethod
    def setUpClassBaseData(cls, *args, **kwargs):
        super().setUpClassBaseData(*args, **kwargs)
        cls.product_z = (
            cls.env["product.product"]
            .sudo()
            .create(
                {
                    "name": "Product Z",
                    "type": "product",
                    "default_code": "Z",
                    "barcode": "Z",
                    "weight": 7,
                }
            )
        )
        cls.picking_z = cls._create_picking(lines=[(cls.product_z, 40)])
        cls._update_qty_in_location(cls.zone_sublocation1, cls.product_z, 32)

    def setUp(self):
        super().setUp()
        self.service.work.current_picking_type = self.picking1.picking_type_id

    def test_unload_set_destination_wrong_parameters(self):
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        response = self.service.dispatch(
            "unload_set_destination",
            params={"package_id": 1234567890, "barcode": "BARCODE"},
        )
        move_lines = self.service._find_location_move_lines()
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
            move_line,
            move_line.reserved_uom_qty,
            self.free_package,
        )
        response = self.service.dispatch(
            "unload_set_destination",
            params={"package_id": self.free_package.id, "barcode": "UNKNOWN"},
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
            move_line,
            move_line.reserved_uom_qty,
            self.free_package,
        )
        response = self.service.dispatch(
            "unload_set_destination",
            params={
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

    def test_unload_set_destination_location_move_not_allowed(self):
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        move_line = self.picking1.move_line_ids
        move_line[0].move_id.location_dest_id = self.packing_sublocation_a
        move_line[0].picking_id.location_dest_id = self.packing_sublocation_a
        # set the destination package
        self.service._set_destination_package(
            move_line,
            move_line.reserved_uom_qty,
            self.free_package,
        )
        response = self.service.dispatch(
            "unload_set_destination",
            params={
                "package_id": self.free_package.id,
                "barcode": self.packing_sublocation_b.barcode,
            },
        )
        self.assert_response_unload_set_destination(
            response,
            zone_location,
            picking_type,
            move_line,
            message=self.service.msg_store.dest_location_not_allowed(),
        )
        # Ensure that when unload_package_at_destination is False,
        # the result_package_id remains.
        self.assertEqual(move_line.result_package_id, self.free_package)

    def test_unload_set_destination_unload_package_enabled(self):
        move_line = self.picking1.move_line_ids
        packing_sublocation1 = (
            self.env["stock.location"]
            .sudo()
            .create(
                {
                    "name": "Packing sublocation-1",
                    "location_id": self.packing_location.id,
                    "barcode": "PACKING_SUBLOCATIO_1",
                }
            )
        )
        packing_sublocation2 = (
            self.env["stock.location"]
            .sudo()
            .create(
                {
                    "name": "Packing sublocation-2",
                    "location_id": self.packing_location.id,
                    "barcode": "PACKING_SUBLOCATIO_2",
                }
            )
        )
        # set the destination package
        self.service._set_destination_package(
            move_line,
            move_line.reserved_uom_qty,
            self.free_package,
        )
        move_line.location_dest_id = packing_sublocation1
        # Enable unload_package_at_destination
        self.menu.sudo().write({"unload_package_at_destination": True})
        self.service.dispatch(
            "unload_set_destination",
            params={
                "package_id": self.free_package.id,
                "barcode": packing_sublocation2.barcode,
                "confirmation": packing_sublocation2.barcode,
            },
        )
        # Response has already been tested in the test above
        # result package should be False
        self.assertFalse(move_line.result_package_id)

    def test_unload_set_destination_confirm_location(self):
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        move_line = self.picking1.move_line_ids
        packing_sublocation1 = (
            self.env["stock.location"]
            .sudo()
            .create(
                {
                    "name": "Packing sublocation-1",
                    "location_id": self.packing_location.id,
                    "barcode": "PACKING_SUBLOCATIO_1",
                }
            )
        )
        packing_sublocation2 = (
            self.env["stock.location"]
            .sudo()
            .create(
                {
                    "name": "Packing sublocation-2",
                    "location_id": self.packing_location.id,
                    "barcode": "PACKING_SUBLOCATIO_2",
                }
            )
        )
        # set the destination package
        self.service._set_destination_package(
            move_line,
            move_line.reserved_uom_qty,
            self.free_package,
        )
        move_line.location_dest_id = packing_sublocation1
        response = self.service.dispatch(
            "unload_set_destination",
            params={
                "package_id": self.free_package.id,
                "barcode": packing_sublocation2.barcode,
            },
        )
        self.assert_response_unload_set_destination(
            response,
            zone_location,
            picking_type,
            move_line,
            message=self.service.msg_store.confirm_location_changed(
                packing_sublocation1, packing_sublocation2
            ),
            confirmation_required=packing_sublocation2.barcode,
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
            move_line,
            move_line.reserved_uom_qty,
            self.free_package,
        )
        response = self.service.dispatch(
            "unload_set_destination",
            params={
                "package_id": self.free_package.id,
                "barcode": packing_sublocation.barcode,
                "confirmation": packing_sublocation.barcode,
            },
        )
        # check data
        self.assertEqual(move_line.location_dest_id, packing_sublocation)
        self.assertEqual(move_line.move_id.state, "done")
        # check response
        move_lines = self.service._find_location_move_lines()
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
        move_lines = self.picking5.move_line_ids
        for move_line, package_dest in zip(
            move_lines, self.free_package | self.another_package
        ):
            self.service._set_destination_package(
                move_line,
                move_line.reserved_uom_qty,
                package_dest,
            )
        free_package_line = move_lines.filtered(
            lambda l: l.result_package_id == self.free_package
        )
        another_package_line = move_lines - free_package_line

        # process 1/2 buffer line
        response = self.service.dispatch(
            "unload_set_destination",
            params={
                "package_id": self.free_package.id,
                "barcode": self.packing_location.barcode,
            },
        )
        # check data
        done_picking = self.picking5.backorder_ids
        self.assertEqual(done_picking.state, "done")
        self.assertEqual(done_picking.move_line_ids, free_package_line)

        self.assertEqual(free_package_line.location_dest_id, self.packing_location)
        self.assertEqual(free_package_line.move_id.state, "done")

        self.assertEqual(self.picking5.move_line_ids, another_package_line)

        # check response
        buffer_line = self.service._find_buffer_move_lines()
        completion_info = self.service._actions_for("completion.info")
        completion_info_popup = completion_info.popup(buffer_line)
        self.assert_response_unload_single(
            response,
            zone_location,
            picking_type,
            buffer_line,
            popup=completion_info_popup,
        )

    def test_unload_set_destination_partially_available_backorder(self):
        zone_location = self.zone_location
        picking_type = self.picking_z.picking_type_id
        self.assertEqual(self.picking_z.move_ids[0].product_uom_qty, 40)
        self.picking_z.action_assign()
        move_line = self.picking_z.move_line_ids
        self.assertEqual(move_line.reserved_uom_qty, 32)
        self.assertEqual(move_line.move_id.state, "partially_available")
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
            move_line,
            move_line.reserved_uom_qty,
            self.free_package,
        )
        response = self.service.dispatch(
            "unload_set_destination",
            params={
                "package_id": self.free_package.id,
                "barcode": packing_sublocation.barcode,
                "confirmation": packing_sublocation.barcode,
            },
        )
        # check data
        # move line has been moved to a new picking
        # move line has been validated in the new picking
        self.assertNotEqual(move_line.move_id.picking_id, self.picking_z)
        backorder = move_line.move_id.picking_id.backorder_id
        self.assertEqual(backorder, self.picking_z)
        # the backorder contains a new line w/ the rest of the qty
        # that couldn't be processed
        self.assertEqual(backorder.move_ids[0].product_uom_qty, 8)
        self.assertEqual(backorder.state, "confirmed")
        # the line has been processed
        self.assertEqual(move_line.location_dest_id, packing_sublocation)
        self.assertEqual(move_line.move_id.state, "done")
        # check response
        move_lines = self.service._find_location_move_lines()
        self.assert_response_select_line(
            response,
            zone_location,
            picking_type,
            move_lines,
            message=self.service.msg_store.buffer_complete(),
        )
