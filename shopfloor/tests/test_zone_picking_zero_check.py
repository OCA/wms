# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from .test_zone_picking_base import ZonePickingCommonCase


# pylint: disable=missing-return
class ZonePickingZeroCheckCase(ZonePickingCommonCase):
    """Tests for endpoint used from zero_check

    * /is_zero

    """

    def setUp(self):
        super().setUp()
        self.service.work.current_picking_type = self.picking1.picking_type_id

    def test_is_zero_wrong_parameters(self):
        response = self.service.dispatch(
            "is_zero",
            params={"move_line_id": 1234567890, "zero": True},
        )
        self.assert_response_start(
            response,
            message=self.service.msg_store.record_not_found(),
        )

    def test_is_zero_is_empty(self):
        """call /is_zero confirming it's empty"""
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        move_line = self.picking1.move_line_ids[0]
        response = self.service.dispatch(
            "is_zero",
            params={"move_line_id": move_line.id, "zero": True},
        )
        move_lines = self.service._find_location_move_lines()
        self.assert_response_select_line(
            response,
            zone_location,
            picking_type,
            move_lines,
        )
