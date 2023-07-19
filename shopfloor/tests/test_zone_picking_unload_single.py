# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from .test_zone_picking_base import ZonePickingCommonCase

# pylint: disable=missing-return


class ZonePickingUnloadSingleCase(ZonePickingCommonCase):
    """Tests for endpoint used from unload_single

    * /unload_scan_pack

    """

    def setUp(self):
        super().setUp()
        self.service.work.current_picking_type = self.picking1.picking_type_id

    def test_unload_scan_pack_wrong_parameters(self):
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        move_line = self.picking1.move_line_ids
        # wrong package ID, and there is still a move line to unload
        # => get back on 'unload_single' screen
        self.service._set_destination_package(
            move_line,
            move_line.reserved_uom_qty,
            self.free_package,
        )
        response = self.service.dispatch(
            "unload_scan_pack",
            params={"package_id": 1234567890, "barcode": "UNKNOWN"},
        )
        completion_info = self.service._actions_for("completion.info")
        completion_info_popup = completion_info.popup(move_line)
        self.assert_response_unload_single(
            response,
            zone_location,
            picking_type,
            move_line,
            message=self.service.msg_store.record_not_found(),
            popup=completion_info_popup,
        )
        # wrong package ID, and there is no more move line to unload from the buffer
        # => get back on 'select_line' screen
        move_line.write(
            {"qty_done": 0, "shopfloor_user_id": False, "result_package_id": False}
        )
        response = self.service.dispatch(
            "unload_scan_pack",
            params={"package_id": 1234567890, "barcode": "UNKNOWN"},
        )
        move_lines = self.service._find_location_move_lines()
        self.assert_response_select_line(
            response,
            zone_location,
            picking_type,
            move_lines,
            message=self.service.msg_store.buffer_complete(),
        )
        # wrong package ID, and there is no more move line to process in picking type
        # => get back on 'start' screen
        self.pickings.move_ids._do_unreserve()
        response = self.service.dispatch(
            "unload_scan_pack",
            params={"package_id": 1234567890, "barcode": "UNKNOWN"},
        )
        self.assert_response_start(
            response,
            message=self.service.msg_store.picking_type_complete(picking_type),
        )

    def test_unload_scan_pack_barcode_match(self):
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
            "unload_scan_pack",
            params={
                "package_id": move_line.result_package_id.id,
                "barcode": self.free_package.name,
            },
        )
        self.assert_response_unload_set_destination(
            response,
            zone_location,
            picking_type,
            move_line,
        )

    def test_unload_scan_pack_barcode_not_match(self):
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        move_line = self.picking1.move_line_ids
        self.wrong_package = self.env["stock.quant.package"].create(
            {"name": "WRONG_PACKAGE"}
        )
        # set the destination package
        self.service._set_destination_package(
            move_line,
            move_line.reserved_uom_qty,
            self.free_package,
        )
        response = self.service.dispatch(
            "unload_scan_pack",
            params={
                "package_id": move_line.result_package_id.id,
                "barcode": self.wrong_package.name,
            },
        )
        self.assert_response_unload_single(
            response,
            zone_location,
            picking_type,
            move_line,
            message=self.service.msg_store.barcode_no_match(self.free_package.name),
        )
