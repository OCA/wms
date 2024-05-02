# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from .test_zone_picking_base import ZonePickingCommonCase


# pylint: disable=missing-return
class ZonePickingStockIssueCase(ZonePickingCommonCase):
    """Tests for endpoint used from stock_issue

    * /stock_issue

    """

    def setUp(self):
        super().setUp()
        self.service.work.current_picking_type = self.picking1.picking_type_id

    def test_stock_issue_wrong_parameters(self):
        response = self.service.dispatch(
            "stock_issue",
            params={"move_line_id": 1234567890},
        )
        self.assert_response_start(
            response,
            message=self.service.msg_store.record_not_found(),
        )

    def test_stock_issue_no_more_reservation(self):
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        move_line = self.picking1.move_line_ids[0]
        move = move_line.move_id
        response = self.service.dispatch(
            "stock_issue",
            params={"move_line_id": move_line.id},
        )
        self.assertFalse(move_line.exists())
        self.assertFalse(move.move_line_ids)
        move_lines = self.service._find_location_move_lines()
        self.assert_response_select_line(
            response,
            zone_location,
            picking_type,
            move_lines,
        )

    def test_stock_issue1(self):
        """Once the stock issue is done, the move can't be reserved anymore."""
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        move_line = self.picking1.move_line_ids[0]
        move = move_line.move_id
        response = self.service.dispatch(
            "stock_issue",
            params={"move_line_id": move_line.id},
        )
        self.assertFalse(move_line.exists())
        self.assertFalse(move.move_line_ids)
        move_lines = self.service._find_location_move_lines()
        self.assert_response_select_line(
            response,
            zone_location,
            picking_type,
            move_lines,
        )

    def test_stock_issue2(self):
        """Once the stock issue is done, the move has been reserved again."""
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        move_line = self.picking1.move_line_ids[0]
        location = move_line.location_id
        move = move_line.move_id
        quants_before = self.env["stock.quant"].search(
            [("location_id", "=", location.id), ("product_id", "=", move.product_id.id)]
        )
        # Increase the quantity in the current location
        self._update_qty_in_location(location, move.product_id, 100)
        response = self.service.dispatch(
            "stock_issue",
            params={"move_line_id": move_line.id},
        )
        self.assertFalse(move_line.exists())
        self.assertTrue(move.move_line_ids)
        self.assertEqual(move.move_line_ids.location_id, location)
        self.assert_response_set_line_destination(
            response,
            zone_location,
            picking_type,
            move.move_line_ids,
        )
        # Check the inventory
        quants_after = self.env["stock.quant"].search(
            [("location_id", "=", location.id), ("product_id", "=", move.product_id.id)]
        )
        inventory_quant = quants_after - quants_before
        self.assertTrue(inventory_quant)

    def test_stock_issue3(self):
        """Once the stock issue is done, the move has been reserved again
        but from another location.
        """
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        move_line = self.picking1.move_line_ids[0]
        move = move_line.move_id
        # Put some quantity in another location to get a new reservations from there
        self._update_qty_in_location(self.zone_sublocation2, move.product_id, 10)
        response = self.service.dispatch(
            "stock_issue",
            params={"move_line_id": move_line.id},
        )
        self.assertFalse(move_line.exists())
        self.assertTrue(move.move_line_ids)
        self.assertEqual(move.move_line_ids.location_id, self.zone_sublocation2)
        self.assert_response_set_line_destination(
            response,
            zone_location,
            picking_type,
            move.move_line_ids,
        )
