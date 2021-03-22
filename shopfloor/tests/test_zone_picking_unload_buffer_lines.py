# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from .test_zone_picking_base import ZonePickingCommonCase


class ZonePickingUnloadBufferLinesCase(ZonePickingCommonCase):
    """Tests buffer lines to unload are retrieved properly.

    Buffer lines are the lines processed during zone picking work.
    At the end of her/his work, the user can unload all processed lines
    in one or more destination.

    Here we make sure all the lines are processable.
    """

    def setUp(self):
        super().setUp()
        self.service.work.current_picking_type = self.picking1.picking_type_id

    def test_find_buffer_lines1(self):
        move_lines = (
            self.picking1.move_line_ids
            | self.picking2.move_line_ids
            | self.picking3.move_line_ids
            | self.picking4.move_line_ids
        )
        zones = move_lines.mapped("location_id")
        # we work on lines coming from 4 different locations
        self.assertEqual(len(zones), 4)
        # Process them all (simulate)
        for i, line in enumerate(move_lines):
            dest_package = self.env["stock.quant.package"].create(
                {"name": f"TEST PKG {i}"}
            )
            self.service._set_destination_package(
                line, line.product_uom_qty, dest_package,
            )

        # We can unload all the lines no matter which zone we are before unload
        for zone in zones:
            self.service.work.current_zone_location = zone
            self.assertEqual(self.service._find_buffer_move_lines(), move_lines)

    def test_find_buffer_lines2(self):
        # Skip lines from picking1
        move_lines = (
            self.picking2.move_line_ids
            | self.picking3.move_line_ids
            | self.picking4.move_line_ids
        )
        zones = move_lines.mapped("location_id")
        # we work on lines coming from 3 different locations
        self.assertEqual(len(zones), 3)
        # Process them all (simulate)
        for i, line in enumerate(move_lines):
            dest_package = self.env["stock.quant.package"].create(
                {"name": f"TEST PKG {i}"}
            )
            self.service._set_destination_package(
                line, line.product_uom_qty, dest_package,
            )

        # We can unload all the lines no matter which zone we are before unload
        for zone in zones:
            self.service.work.current_zone_location = zone
            self.assertEqual(self.service._find_buffer_move_lines(), move_lines)
            self.assertNotIn(
                self.picking1.move_line_ids, self.service._find_buffer_move_lines()
            )

    def test_find_buffer_lines3(self):
        move_lines = (
            self.picking2.move_line_ids
            | self.picking3.move_line_ids
            | self.picking4.move_line_ids
        )
        zones = move_lines.mapped("location_id")
        # we work on lines coming from 4 different locations
        self.assertEqual(len(zones), 3)
        # Process them all (simulate)
        for i, line in enumerate(move_lines):
            dest_package = self.env["stock.quant.package"].create(
                {"name": f"TEST PKG {i}"}
            )
            self.service._set_destination_package(
                line, line.product_uom_qty, dest_package,
            )
        # Simulate line from picking1 processed by another user
        for i, line in enumerate(self.picking1.move_line_ids):
            dest_package = self.env["stock.quant.package"].create(
                {"name": f"TEST PKG 1 {i}"}
            )
            self.service._set_move_line_as_done(
                line,
                line.product_uom_qty,
                dest_package,
                user=self.env.ref("base.user_admin"),
            )

        # We can unload all the lines no matter which zone we are before unload
        for zone in zones:
            self.service.work.current_zone_location = zone
            self.assertEqual(self.service._find_buffer_move_lines(), move_lines)
            self.assertNotIn(
                self.picking1.move_line_ids, self.service._find_buffer_move_lines()
            )
