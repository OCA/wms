# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from .test_zone_picking_base import ZonePickingCommonCase


class ZonePickingSetLineDestinationPackageNotAllowedCase(ZonePickingCommonCase):
    """Tests for endpoint used from set_line_destination

    With the allow scan destination package option disabled

    * /set_destination

    """

    def setUp(self):
        super().setUp()
        self.service.work.current_picking_type = self.picking1.picking_type_id
        self.menu.sudo().allow_alternative_destination_package = False

    def test_set_destination_alternative_package_not_allowed_scan_package_whole_qty(
        self,
    ):
        # If option allow_alternative_destination_package is not allowed
        # and the user scans a whole package,
        # they should not be allowed to do the move.
        move_line = self.picking1.move_line_ids[0]
        response = self.service.dispatch(
            "set_destination",
            params={
                "move_line_id": move_line.id,
                "barcode": self.free_package.name,
                "quantity": move_line.reserved_uom_qty,
                "confirmation": None,
            },
        )
        self.assert_response_set_line_destination(
            response,
            zone_location=self.zone_location,
            picking_type=self.picking_type,
            move_line=move_line,
            qty_done=10.0,
            message=self.service.msg_store.package_transfer_not_allowed_scan_location(),
        )

    def test_set_destination_alternative_package_not_allowed_scan_package_partial_qty(
        self,
    ):
        # If option allow_alternative_destination_package is not allowed
        # and the user scans a partial package,
        # they should be allowed to do the move.
        move_line = self.picking1.move_line_ids[0]
        response = self.service.dispatch(
            "set_destination",
            params={
                "move_line_id": move_line.id,
                "barcode": self.free_package.name,
                "quantity": 1.0,
                "confirmation": None,
            },
        )
        move_lines = self.service._find_location_move_lines()
        move_lines = move_lines.sorted(lambda l: l.move_id.priority, reverse=True)
        self.assert_response_set_line_destination(
            response,
            zone_location=self.zone_location,
            picking_type=self.picking_type,
            move_line=move_line,
            qty_done=1.0,
            message=self.service.msg_store.package_transfer_not_allowed_scan_location(),
        )

    def test_set_destination_alternative_package_not_allowed_scan_location(self):
        # If option allow_alternative_destination_package is not allowed,
        # and the user scans a location,
        # they should be allowed to do the move.
        move_line = self.picking1.move_line_ids[0]
        response = self.service.dispatch(
            "set_destination",
            params={
                "move_line_id": move_line.id,
                "barcode": self.packing_location.barcode,
                "quantity": move_line.reserved_uom_qty,
                "confirmation": None,
            },
        )
        move_lines = self.service._find_location_move_lines()
        move_lines = move_lines.sorted(lambda l: l.move_id.priority, reverse=True)
        self.assert_response_select_line(
            response,
            zone_location=self.zone_location,
            picking_type=self.picking_type,
            move_lines=move_lines,
            message=self.service.msg_store.confirm_pack_moved(),
        )
