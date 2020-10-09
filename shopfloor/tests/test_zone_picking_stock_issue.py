# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from .test_zone_picking_base import ZonePickingCommonCase


class ZonePickingStockIssueCase(ZonePickingCommonCase):
    """Tests for endpoint used from stock_issue

    * /stock_issue

    """

    def test_stock_issue_wrong_parameters(self):
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        move_line = self.picking1.move_line_ids[0]
        response = self.service.dispatch(
            "stock_issue",
            params={
                "zone_location_id": 1234567890,
                "picking_type_id": picking_type.id,
                "move_line_id": move_line.id,
            },
        )
        self.assert_response_start(
            response, message=self.service.msg_store.record_not_found(),
        )
        response = self.service.dispatch(
            "stock_issue",
            params={
                "zone_location_id": zone_location.id,
                "picking_type_id": 1234567890,
                "move_line_id": move_line.id,
            },
        )
        self.assert_response_start(
            response, message=self.service.msg_store.record_not_found(),
        )
        response = self.service.dispatch(
            "stock_issue",
            params={
                "zone_location_id": zone_location.id,
                "picking_type_id": picking_type.id,
                "move_line_id": 1234567890,
            },
        )
        self.assert_response_start(
            response, message=self.service.msg_store.record_not_found(),
        )

    def test_stock_issue_no_more_reservation(self):
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        move_line = self.picking1.move_line_ids[0]
        move = move_line.move_id
        response = self.service.dispatch(
            "stock_issue",
            params={
                "zone_location_id": zone_location.id,
                "picking_type_id": picking_type.id,
                "move_line_id": move_line.id,
            },
        )
        self.assertFalse(move_line.exists())
        self.assertFalse(move.move_line_ids)
        move_lines = self.service._find_location_move_lines(zone_location, picking_type)
        self.assert_response_select_line(
            response, zone_location, picking_type, move_lines,
        )

    def test_stock_issue1(self):
        """Once the stock issue is done, the move can't be reserved anymore."""
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        move_line = self.picking1.move_line_ids[0]
        location = move_line.location_id
        move = move_line.move_id
        response = self.service.dispatch(
            "stock_issue",
            params={
                "zone_location_id": zone_location.id,
                "picking_type_id": picking_type.id,
                "move_line_id": move_line.id,
            },
        )
        self.assertFalse(move_line.exists())
        self.assertFalse(move.move_line_ids)
        move_lines = self.service._find_location_move_lines(zone_location, picking_type)
        self.assert_response_select_line(
            response, zone_location, picking_type, move_lines,
        )
        # Check that the inventory exists
        inventory = self.env["stock.inventory"].search(
            [
                (
                    "name",
                    "ilike",
                    "{} stock correction in location {}".format(
                        move.picking_id.name, location.name
                    ),
                ),
                ("state", "=", "done"),
                ("line_ids.location_id", "in", location.ids),
                ("line_ids.product_id", "in", move.product_id.ids),
            ]
        )
        self.assertTrue(inventory)
        self.assertEqual(inventory.line_ids.product_id, move.product_id)
        self.assertEqual(inventory.line_ids.product_qty, 0)

    def test_stock_issue2(self):
        """Once the stock issue is done, the move has been reserved again."""
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        move_line = self.picking1.move_line_ids[0]
        location = move_line.location_id
        move = move_line.move_id
        # Increase the quantity in the current location
        self._update_qty_in_location(location, move.product_id, 100)
        response = self.service.dispatch(
            "stock_issue",
            params={
                "zone_location_id": zone_location.id,
                "picking_type_id": picking_type.id,
                "move_line_id": move_line.id,
            },
        )
        self.assertFalse(move_line.exists())
        self.assertTrue(move.move_line_ids)
        self.assertEqual(move.move_line_ids.location_id, location)
        self.assert_response_set_line_destination(
            response, zone_location, picking_type, move.move_line_ids,
        )
        # Check the inventory
        inventory = self.env["stock.inventory"].search(
            [
                (
                    "name",
                    "ilike",
                    "{} stock correction in location {}".format(
                        move.picking_id.name, location.name
                    ),
                ),
                ("state", "=", "done"),
                ("line_ids.location_id", "in", location.ids),
                ("line_ids.product_id", "in", move.product_id.ids),
            ]
        )
        self.assertTrue(inventory)
        self.assertEqual(inventory.line_ids.product_id, move.product_id)
        self.assertEqual(inventory.line_ids.product_qty, 0)

    def test_stock_issue3(self):
        """Once the stock issue is done, the move has been reserved again
        but from another location.
        """
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        move_line = self.picking1.move_line_ids[0]
        location = move_line.location_id
        move = move_line.move_id
        # Put some quantity in another location to get a new reservations from there
        self._update_qty_in_location(self.zone_sublocation2, move.product_id, 10)
        response = self.service.dispatch(
            "stock_issue",
            params={
                "zone_location_id": zone_location.id,
                "picking_type_id": picking_type.id,
                "move_line_id": move_line.id,
            },
        )
        self.assertFalse(move_line.exists())
        self.assertTrue(move.move_line_ids)
        self.assertEqual(move.move_line_ids.location_id, self.zone_sublocation2)
        self.assert_response_set_line_destination(
            response, zone_location, picking_type, move.move_line_ids,
        )
        # Check the inventory
        inventory = self.env["stock.inventory"].search(
            [
                (
                    "name",
                    "ilike",
                    "{} stock correction in location {}".format(
                        move.picking_id.name, location.name
                    ),
                ),
                ("state", "=", "done"),
                ("line_ids.location_id", "in", location.ids),
                ("line_ids.product_id", "in", move.product_id.ids),
            ]
        )
        self.assertTrue(inventory)
        self.assertEqual(inventory.line_ids.product_id, move.product_id)
        self.assertEqual(inventory.line_ids.product_qty, 0)
