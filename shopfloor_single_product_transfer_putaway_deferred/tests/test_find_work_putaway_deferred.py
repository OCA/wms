# Copyright 2026 ACSONE SA/NV <https://www.acsone.eu>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields

from odoo.addons.shopfloor_single_product_transfer.tests.common import CommonCase


class TestFindWorkPutawayDeferred(CommonCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.menu.sudo().allow_get_work = True
        cls.picking_type.sudo().defer_putaway_to_operator = True
        cls.default_dest = cls.picking_type.default_location_dest_id
        # Sub-location used as the putaway target for product_a
        cls.putaway_sublocation = (
            cls.env["stock.location"]
            .sudo()
            .create(
                {
                    "name": "Putaway Target",
                    "location_id": cls.default_dest.id,
                    "usage": "internal",
                }
            )
        )
        # Putaway rule: product_a → putaway_sublocation (product_b has no rule)
        cls.putaway_rule = (
            cls.env["stock.putaway.rule"]
            .sudo()
            .create(
                {
                    "product_id": cls.product_a.id,
                    "location_in_id": cls.default_dest.id,
                    "location_out_id": cls.putaway_sublocation.id,
                }
            )
        )
        cls._add_stock_to_product(cls.product_a, cls.location_src, 10)
        cls._add_stock_to_product(cls.product_b, cls.location_src, 10)

    def _data_for_start_line(
        self, move_line, selected_location_id=None, selected_package_id=None
    ):
        return {
            "move_line": self._data_for_move_line(move_line),
            "selected_location_id": selected_location_id,
            "selected_package_id": selected_package_id,
            "scan_location_or_pack_first": self.menu.scan_location_or_pack_first,
        }

    def test_find_work_deferred_putaway_recomputes_destination(self):
        """find_work triggers _recompute_putaways on a deferred line."""
        self.assertFalse(self.menu.ignore_no_putaway_available)
        picking = self._create_picking(lines=[(self.product_a, 5)])
        move_line = fields.first(picking.move_line_ids)

        # After action_assign with defer_putaway_to_operator=True the line is
        # deferred: putaway strategy has not been applied yet.
        self.assertTrue(move_line.putaway_deferred)
        self.assertEqual(move_line.location_dest_id, self.default_dest)

        response = self.service.dispatch("find_work")

        # _try_select_move_line must have called _recompute_putaways().
        self.assertFalse(move_line.putaway_deferred)
        self.assertEqual(move_line.location_dest_id, self.putaway_sublocation)
        self.assert_response(
            response,
            next_state="start_line",
            data=self._data_for_start_line(move_line),
        )

    def test_find_work_deferred_putaway_no_rule_returns_no_putaway_error(self):
        """
        find_work recomputes but no matching rule: returns no_putaway_destination_available.
        """
        self.assertFalse(self.menu.ignore_no_putaway_available)
        picking = self._create_picking(lines=[(self.product_b, 5)])
        move_line = fields.first(picking.move_line_ids)

        self.assertTrue(move_line.putaway_deferred)
        self.assertEqual(move_line.location_dest_id, self.default_dest)

        response = self.service.dispatch("find_work")

        # Deferred flag is cleared even when no rule matched.
        self.assertFalse(move_line.putaway_deferred)
        self.assertEqual(move_line.location_dest_id, self.default_dest)
        self.assert_response(
            response,
            next_state="get_work",
            message=self.msg_store.no_putaway_destination_available(),
        )

    def test_find_work_deferred_no_rule_ignore_putaway_returns_no_work(self):
        """With ignore_no_putaway_available a deferred line without rule is skipped."""
        self._enable_ignore_no_putaway_available()
        picking = self._create_picking(lines=[(self.product_b, 5)])
        move_line = fields.first(picking.move_line_ids)

        self.assertTrue(move_line.putaway_deferred)

        response = self.service.dispatch("find_work")

        # Recompute was triggered; deferred flag cleared.
        self.assertFalse(move_line.putaway_deferred)
        self.assert_response(
            response,
            next_state="get_work",
            message=self.msg_store.no_work_found(),
        )

    def test_find_work_deferred_no_rule_skip_to_next_line(self):
        """
        With ignore_no_putaway_available a deferred line without rule triggers recompute and is
        skipped.
        """
        self._enable_ignore_no_putaway_available()
        self.picking_type.sudo().allow_to_recompute_putaways = True
        # Create a picking with 2 lines: the first one is deferred without rule, the second
        # one has a putaway rule.
        picking = self._create_picking(lines=[(self.product_b, 5)])
        picking2 = self._create_picking(lines=[(self.product_a, 5)])
        move_line_1 = fields.first(picking.move_line_ids)
        move_line_2 = fields.first(picking2.move_line_ids)

        self.assertTrue(move_line_1.putaway_deferred)
        self.assertTrue(move_line_2.putaway_deferred)
        self.assertEqual(move_line_1.location_dest_id, self.default_dest)
        self.assertEqual(move_line_2.location_dest_id, self.default_dest)

        response = self.service.dispatch("find_work")

        # First line was recomputed and skipped; second line was recomputed and selected.
        self.assertFalse(move_line_1.putaway_deferred)
        self.assertFalse(move_line_2.putaway_deferred)
        self.assertEqual(move_line_1.location_dest_id, self.default_dest)
        self.assertEqual(move_line_2.location_dest_id, self.putaway_sublocation)
        self.assert_response(
            response,
            next_state="start_line",
            data=self._data_for_start_line(move_line_2),
        )

        # if we add a rule for the first line, it should be proposed at next find_work
        self.putaway_rule.write({"product_id": self.product_b.id})
        response = self.service.dispatch("find_work")
        self.assertEqual(move_line_1.location_dest_id, self.putaway_sublocation)
        self.assert_response(
            response,
            next_state="start_line",
            data=self._data_for_start_line(move_line_1),
        )

    def test_find_work_ignore_putaway_triggers_recompute(self):
        """With ignore_no_putaway_available, a line with no destination triggers recompute."""
        self._enable_ignore_no_putaway_available()
        self.picking_type.sudo().write(
            {"defer_putaway_to_operator": False, "allow_to_recompute_putaways": True}
        )
        picking = self._create_picking(lines=[(self.product_a, 5)])
        move_line = fields.first(picking.move_line_ids)

        # Force destination back to the default to simulate a line without a
        # putaway destination
        move_line.location_dest_id = self.default_dest
        self.assertFalse(move_line.putaway_deferred)
        self.assertEqual(move_line.location_dest_id, self.default_dest)

        response = self.service.dispatch("find_work")

        # elif branch triggered _recompute_putaways(); rule now applied.
        self.assertEqual(move_line.location_dest_id, self.putaway_sublocation)
        self.assert_response(
            response,
            next_state="start_line",
            data=self._data_for_start_line(move_line),
        )
