# Copyright 2023 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from .test_zone_picking_base import ZonePickingCommonCase


class ZonePickingCompleteMixPackageFluxCase(ZonePickingCommonCase):
    """Tests for the flux of complete mix packages."""

    def setUp(self):
        super().setUp()
        self.service.work.current_picking_type = self.picking1.picking_type_id

    def test_scan_source_and_set_destination_on_mixed_package(self):
        package = self.picking5.package_level_ids[0].package_id
        self.assertTrue(len(package.move_line_ids.product_id) > 1)
        response = self.service.dispatch(
            "scan_source",
            params={"barcode": package.name},
        )
        self.assertTrue(
            response["data"]["set_line_destination"]["handle_complete_mix_pack"]
        )
        move_lines = self.service._find_location_move_lines(
            package=package,
        )
        move_lines = move_lines.sorted(lambda l: l.move_id.priority, reverse=True)
        move_line = move_lines[0]
        self.assert_response_set_line_destination(
            response,
            zone_location=self.zone_location,
            picking_type=self.picking_type,
            move_line=move_line,
            qty_done=0,
            handle_complete_mix_pack=True,
        )
        # Lets move this pack somwehere...
        move_line.location_dest_id = self.shelf1
        quantity_done = move_line.reserved_uom_qty
        response = self.service.dispatch(
            "set_destination",
            params={
                "move_line_id": move_line.id,
                "barcode": self.packing_location.barcode,
                "quantity": quantity_done,
                "confirmation": self.packing_location.barcode,
                "handle_complete_mix_pack": True,
            },
        )
        # Check response
        move_lines = self.service._find_location_move_lines()
        move_lines = move_lines.sorted(lambda l: l.move_id.priority, reverse=True)
        self.assert_response_select_line(
            response,
            zone_location=self.zone_location,
            picking_type=self.picking_type,
            move_lines=move_lines,
            message=self.service.msg_store.confirm_pack_moved(),
        )
