# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from .test_zone_picking_base import ZonePickingCommonCase


class ZonePickingZeroCheckCase(ZonePickingCommonCase):
    """Tests for endpoint used from zero_check

    * /is_zero

    """

    def test_is_zero_wrong_parameters(self):
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        move_line = self.picking1.move_line_ids[0]
        response = self.service.dispatch(
            "is_zero",
            params={
                "zone_location_id": 1234567890,
                "picking_type_id": picking_type.id,
                "move_line_id": move_line.id,
                "zero": True,
            },
        )
        self.assert_response_start(
            response, message=self.service.msg_store.record_not_found(),
        )
        response = self.service.dispatch(
            "is_zero",
            params={
                "zone_location_id": zone_location.id,
                "picking_type_id": 1234567890,
                "move_line_id": move_line.id,
                "zero": True,
            },
        )
        self.assert_response_start(
            response, message=self.service.msg_store.record_not_found(),
        )
        response = self.service.dispatch(
            "is_zero",
            params={
                "zone_location_id": zone_location.id,
                "picking_type_id": picking_type.id,
                "move_line_id": 1234567890,
                "zero": True,
            },
        )
        self.assert_response_start(
            response, message=self.service.msg_store.record_not_found(),
        )

    def test_is_zero_is_empty(self):
        """call /is_zero confirming it's empty"""
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        move_line = self.picking1.move_line_ids[0]
        response = self.service.dispatch(
            "is_zero",
            params={
                "zone_location_id": zone_location.id,
                "picking_type_id": picking_type.id,
                "move_line_id": move_line.id,
                "zero": True,
            },
        )
        move_lines = self.service._find_location_move_lines(zone_location, picking_type)
        self.assert_response_select_line(
            response, zone_location, picking_type, move_lines,
        )

    def test_is_zero_is_not_empty(self):
        """call /is_zero not confirming it's empty"""
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        move_line = self.picking1.move_line_ids[0]
        response = self.service.dispatch(
            "is_zero",
            params={
                "zone_location_id": zone_location.id,
                "picking_type_id": picking_type.id,
                "move_line_id": move_line.id,
                "zero": False,
            },
        )
        move_lines = self.service._find_location_move_lines(zone_location, picking_type)
        self.assert_response_select_line(
            response, zone_location, picking_type, move_lines,
        )
        inventory = self.env["stock.inventory"].search(
            [
                ("location_ids", "in", move_line.location_id.id),
                # FIXME check 'is_zero' implementation
                # ("product_ids", "in", move_line.product_id.id),
                ("state", "=", "draft"),
            ]
        )
        self.assertTrue(inventory)
        self.assertEqual(
            inventory.name,
            "Zero check issue on location {} ({})".format(
                move_line.location_id.name, picking_type.name,
            ),
        )
