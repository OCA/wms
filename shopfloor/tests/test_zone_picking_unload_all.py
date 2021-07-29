# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from .test_zone_picking_base import ZonePickingCommonCase


class ZonePickingUnloadAllCase(ZonePickingCommonCase):
    """Tests for endpoint used from unload_all

    * /set_destination_all
    * /unload_split

    """

    def setUp(self):
        super().setUp()
        self.service.work.current_picking_type = self.picking1.picking_type_id

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
            move_line1,
            move_line1.product_uom_qty,
            self.free_package,
        )
        self.service._set_destination_package(
            move_line2,
            move_line2.product_uom_qty,
            another_package,
        )
        # set destination location for all lines in the buffer
        response = self.service.dispatch(
            "set_destination_all",
            params={"barcode": self.packing_location.barcode},
        )
        # check response
        buffer_lines = self.service._find_buffer_move_lines()
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
        packing_sublocation1 = (
            self.env["stock.location"]
            .sudo()
            .create(
                {
                    "name": "Packing sublocation-1",
                    "location_id": self.packing_location.id,
                    "barcode": "PACKING_SUBLOCATION_1",
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
                    "barcode": "PACKING_SUBLOCATION_2",
                }
            )
        )
        # set the destination package on lines
        self.service._set_destination_package(
            move_line1,
            move_line1.product_uom_qty,
            self.free_package,
        )
        self.service._set_destination_package(
            move_line2,
            move_line2.product_uom_qty,
            another_package,
        )
        # set an allowed destination location (inside the picking type default
        # destination location) for all lines in the buffer with a non-expected
        # one, meaning a destination which is not a child of the current buffer
        # lines destination
        (move_line1 | move_line2).location_dest_id = packing_sublocation1
        response = self.service.dispatch(
            "set_destination_all",
            params={"barcode": packing_sublocation2.barcode},
        )
        # check response: this destination needs the user confirmation
        buffer_lines = self.service._find_buffer_move_lines()
        self.assert_response_unload_all(
            response,
            zone_location,
            picking_type,
            buffer_lines,
            message=self.service.msg_store.confirm_location_changed(
                packing_sublocation1,
                packing_sublocation2,
            ),
            confirmation_required=True,
        )
        # set an allowed destination location (inside the picking type default
        # destination location) for all lines in the buffer with an expected one
        # meaning a destination which is a child of the current buffer lines
        # destination
        response = self.service.dispatch(
            "set_destination_all",
            params={"barcode": packing_sublocation1.barcode},
        )
        # check response: OK
        move_lines = self.service._find_location_move_lines()
        self.assert_response_select_line(
            response,
            zone_location,
            picking_type,
            move_lines,
            message=self.service.msg_store.buffer_complete(),
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
            move_line1,
            move_line1.product_uom_qty,
            self.free_package,
        )
        self.service._set_destination_package(
            move_line2,
            move_line2.product_uom_qty,
            another_package,
        )
        # set destination location for all lines in the buffer
        response = self.service.dispatch(
            "set_destination_all",
            params={"barcode": self.packing_location.barcode},
        )
        # check data
        self.assertEqual(self.picking5.state, "done")
        # buffer should be empty
        buffer_lines = self.service._find_buffer_move_lines()
        self.assertFalse(buffer_lines)
        # check response
        move_lines = self.service._find_location_move_lines()
        self.assert_response_select_line(
            response,
            zone_location,
            picking_type,
            move_lines,
            message=self.service.msg_store.buffer_complete(),
        )

    def test_set_destination_all_partial_qty_done_ok(self):
        zone_location = self.zone_location
        picking_type = self.picking6.picking_type_id
        move_g = self.picking6.move_lines.filtered(
            lambda m: m.product_id == self.product_g
        )
        move_h = self.picking6.move_lines.filtered(
            lambda m: m.product_id == self.product_h
        )
        self.assertEqual(move_g.state, "assigned")
        self.assertEqual(move_h.state, "partially_available")
        move_line_g = move_g.move_line_ids
        move_line_h = move_h.move_line_ids
        another_package = self.env["stock.quant.package"].create(
            {"name": "ANOTHER_PACKAGE"}
        )
        # set the destination package on lines
        self.service._set_destination_package(
            move_line_g,
            move_line_g.product_uom_qty,
            self.free_package,
        )
        self.service._set_destination_package(
            move_line_h,
            move_line_h.product_uom_qty,
            another_package,  # partial qty
        )
        # set destination location for all lines in the buffer
        response = self.service.dispatch(
            "set_destination_all",
            params={"barcode": self.packing_location.barcode},
        )
        # check data
        #   picking validated
        picking_validated = self.picking6
        self.assertEqual(picking_validated.state, "done")
        self.assertEqual(picking_validated.move_line_ids, move_line_g | move_line_h)
        self.assertEqual(move_line_g.state, "done")
        self.assertEqual(move_line_g.qty_done, 6)
        self.assertEqual(move_line_h.state, "done")
        self.assertEqual(move_line_h.qty_done, 3)
        #   current picking (backorder)
        backorder = self.picking6.backorder_ids
        self.assertEqual(backorder.state, "confirmed")
        self.assertEqual(backorder.move_lines.product_id, self.product_h)
        self.assertEqual(backorder.move_lines.product_uom_qty, 3)
        self.assertFalse(backorder.move_line_ids)
        # buffer should be empty
        buffer_lines = self.service._find_buffer_move_lines()
        self.assertFalse(buffer_lines)
        # check response
        move_lines = self.service._find_location_move_lines()
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
            move_line,
            move_line.product_uom_qty,
            self.free_package,
        )
        response = self.service.dispatch(
            "set_destination_all",
            params={"barcode": self.customer_location.barcode},
        )
        # check response
        buffer_lines = self.service._find_buffer_move_lines()
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
            move_line,
            move_line.product_uom_qty,
            self.free_package,
        )
        response = self.service.dispatch(
            "set_destination_all",
            params={"barcode": "UNKNOWN"},
        )
        # check response
        buffer_lines = self.service._find_buffer_move_lines()
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
            params={},
        )
        # check response
        move_lines = self.service._find_location_move_lines()
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
            move_line,
            move_line.product_uom_qty,
            self.free_package,
        )
        response = self.service.dispatch(
            "unload_split",
            params={},
        )
        # check response
        buffer_lines = self.service._find_buffer_move_lines()
        self.assert_response_unload_set_destination(
            response,
            zone_location,
            picking_type,
            buffer_lines,
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
                move_line,
                move_line.product_uom_qty,
                package_dest,
            )
        response = self.service.dispatch(
            "unload_split",
            params={},
        )
        # check response
        buffer_lines = self.service._find_buffer_move_lines()
        completion_info = self.service._actions_for("completion.info")
        completion_info_popup = completion_info.popup(buffer_lines)
        self.assert_response_unload_single(
            response,
            zone_location,
            picking_type,
            buffer_lines[0],
            popup=completion_info_popup,
        )
