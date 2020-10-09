# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from .test_zone_picking_base import ZonePickingCommonCase


class ZonePickingSelectPickingTypeCase(ZonePickingCommonCase):
    """Tests for endpoint used from select_picking_type

    * /list_move_lines

    """

    def test_list_move_lines_wrong_parameters(self):
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        response = self.service.dispatch(
            "list_move_lines",
            params={
                "zone_location_id": 1234567890,
                "picking_type_id": picking_type.id,
            },
        )
        self.assert_response_start(
            response, message=self.service.msg_store.record_not_found(),
        )
        response = self.service.dispatch(
            "list_move_lines",
            params={
                "zone_location_id": zone_location.id,
                "picking_type_id": 1234567890,
            },
        )
        self.assert_response_start(
            response, message=self.service.msg_store.record_not_found(),
        )

    def test_list_move_lines_ok(self):
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        response = self.service.dispatch(
            "list_move_lines",
            params={
                "zone_location_id": zone_location.id,
                "picking_type_id": picking_type.id,
            },
        )
        move_lines = self.service._find_location_move_lines(zone_location, picking_type)
        self.assert_response_select_line(
            response,
            zone_location=self.zone_location,
            picking_type=self.picking_type,
            move_lines=move_lines,
        )
