# Copyright 2019 Camptocamp (https://www.camptocamp.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from datetime import datetime

from odoo.exceptions import UserError

from .common import PromiseReleaseCommonCase


class TestAvailableToPromiseRelease(PromiseReleaseCommonCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.shipping = cls._out_picking(
            cls._create_picking_chain(
                cls.wh, [(cls.product1, 5)], date=datetime(2019, 9, 2, 16, 0)
            )
        )
        cls._update_qty_in_location(cls.loc_bin1, cls.product1, 15.0)
        cls.wh.delivery_route_id.write(
            {
                "available_to_promise_defer_pull": True,
                "no_backorder_at_release": True,
            }
        )

        cls.shipping.release_available_to_promise()
        cls.picking = cls._prev_picking(cls.shipping)
        cls.picking.action_assign()

    def test_unrelease_full(self):
        """Unrelease all moves of a released ship. The pick should be deleted and
        the moves should be mark as to release"""

        self.assertEqual(self.picking.state, "assigned")
        self.assertRecordValues(
            self.shipping.move_ids,
            [
                {
                    "state": "waiting",
                    "need_release": False,
                    "unrelease_allowed": True,
                }
            ],
        )
        self.shipping.move_ids.unrelease()
        self.assertRecordValues(
            self.shipping.move_ids,
            [
                {
                    "state": "waiting",
                    "need_release": True,
                    "unrelease_allowed": False,
                }
            ],
        )
        self.assertEqual(self.picking.move_ids.state, "cancel")
        self.assertEqual(self.picking.state, "cancel")

        # I can release again the move and a new pick is created
        self.shipping.release_available_to_promise()
        new_picking = self._prev_picking(self.shipping) - self.picking
        self.assertTrue(new_picking)
        self.assertEqual(new_picking.state, "assigned")

    def test_unrelease_partially_processed_move(self):
        """Check it's not possible to unrelease a move that has been partially
        processed"""
        line = self.picking.move_ids.move_line_ids
        line.qty_done = line.reserved_qty - 1
        self.picking.with_context(
            skip_immediate=True, skip_backorder=True
        ).button_validate()
        self.assertEqual(self.picking.state, "done")
        self.assertFalse(self.shipping.move_ids.unrelease_allowed)
        with self.assertRaisesRegex(
            UserError, "You are not allowed to unrelease this move"
        ):
            self.shipping.move_ids.unrelease()

    def test_unrelease_backorder(self):
        """Check the unrelease of a shipping backorder move"""
        # we do a partial pick and validate the picking to create a backorder
        # a validation
        line = self.picking.move_ids.move_line_ids
        line.qty_done = line.reserved_qty - 1
        self.picking.with_context(
            skip_immediate=True, skip_backorder=True
        ).button_validate()
        self.shipping.action_assign()
        line = self.shipping.move_ids.move_line_ids
        line.qty_done = line.reserved_qty
        self.shipping.with_context(
            skip_immediate=True, skip_backorder=True
        ).button_validate()
        # at this stage, our backorder ship move is linked to a pick move to do
        backorder_ship = self.shipping.backorder_ids
        self.assertTrue(backorder_ship)
        self.assertTrue(backorder_ship.move_ids.unrelease_allowed)
        self.assertTrue(
            backorder_ship.move_ids.move_orig_ids.filtered(
                lambda m: m.state not in ("cancel", "done")
            )
        )
        backorder_pick = self._prev_picking(backorder_ship) - self.picking
        self.assertEqual(backorder_pick.state, "assigned")
        backorder_ship.move_ids.unrelease()
        # after the un release, our backorder ship move is not more linked to
        # a pick move to do
        self.assertFalse(backorder_ship.move_ids.unrelease_allowed)
        self.assertEqual(backorder_pick.state, "cancel")
        self.assertFalse(
            backorder_ship.move_ids.move_orig_ids.filtered(
                lambda m: m.state not in ("cancel", "done")
            )
        )

    def test_auto_unrelease_on_backorder(self):
        """Check that moves into a backorder are unreleased if specified on
        the picking type"""
        self.shipping.picking_type_id.unrelease_on_backorder = True
        # we do a partial pick and validate the picking to create a backorder
        # a validation
        line = self.picking.move_ids.move_line_ids
        line.qty_done = line.reserved_qty - 1
        self.picking.with_context(
            skip_immediate=True, skip_backorder=True
        ).button_validate()
        self.shipping.action_assign()
        line = self.shipping.move_ids.move_line_ids
        line.qty_done = line.reserved_qty
        # at this stage, our ship move is linked to a pick move to do
        self.assertTrue(
            self.shipping.move_ids.move_orig_ids.filtered(
                lambda m: m.state not in ("cancel", "done")
            )
        )
        self.shipping.with_context(
            skip_immediate=True, skip_backorder=True
        ).button_validate()
        backorder_ship = self.shipping.backorder_ids
        self.assertTrue(backorder_ship)
        self.assertTrue(backorder_ship.need_release)
        self.assertFalse(backorder_ship.move_ids.unrelease_allowed)
        # no move pick move to do for our move into the backorder
        self.assertFalse(
            backorder_ship.move_ids.move_orig_ids.filtered(
                lambda m: m.state not in ("cancel", "done")
            )
        )
