# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from datetime import datetime

from .common import PromiseReleaseCommonCase


class TestAvailableToPromiseRelease(PromiseReleaseCommonCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        delivery_pick_rule = cls.wh.delivery_route_id.rule_ids.filtered(
            lambda r: r.location_src_id == cls.loc_stock
        )
        delivery_pick_rule.group_propagation_option = "fixed"

        cls.pc1 = cls._create_picking_chain(
            cls.wh, [(cls.product1, 2)], date=datetime(2019, 9, 2, 16, 0)
        )
        cls.shipping1 = cls._out_picking(cls.pc1)
        cls.pc2 = cls._create_picking_chain(
            cls.wh, [(cls.product1, 3)], date=datetime(2019, 9, 2, 16, 0)
        )
        cls.shipping2 = cls._out_picking(cls.pc2)
        cls._update_qty_in_location(cls.loc_bin1, cls.product1, 15.0)
        cls.wh.delivery_route_id.write(
            {
                "available_to_promise_defer_pull": True,
            }
        )
        shippings = cls.shipping1 | cls.shipping2
        cls.deliveries = shippings
        shippings.release_available_to_promise()
        cls.picking1 = cls._prev_picking(cls.shipping1)
        cls.picking1.action_assign()
        cls.picking2 = cls._prev_picking(cls.shipping2)
        cls.picking2.action_assign()

    def test_unrelease_delivery_no_picking_done(self):
        # the picking for delivery 1 and 2 are merged into one move
        # Not the case with stock_group_by_partner_by_carrier
        # self.assertEqual(self.picking1.move_ids.move_line_ids.product_uom_qty, 5)
        self.assertEqual(self.picking1.move_ids.move_dest_ids, self.deliveries.move_ids)
        self.shipping1.unrelease()
        self.assertEqual(len(self.picking1.move_ids), 2)
        move_cancel = self.picking1.move_ids.filtered(lambda m: m.state == "cancel")
        self.assertEqual(move_cancel.product_uom_qty, 2)
        self.assertTrue(self.shipping1.need_release)

    def test_unrelease_after_backorder(self):
        """In this test we all partially process the picking, then validate it
        and create a backorder. Then we partially process the shipping, validate
        it and create a backorder. At this stage we have a backorder shipping
        with a move with 2 origins. The first origin is the processed picking
        and the second origin is the picking to do to complete the backorder
        delivery. At this stage, the unrelease of the backorder shipping should
        be possible.
        """
        # partially process the picking
        self.picking1.move_line_ids[0].qty_done = 1
        # set printed since we are processing the picking
        self.picking1.printed = True
        # validate the picking
        self.picking1.with_context(
            skip_immediate=True, skip_backorder=True
        ).button_validate()
        picking1_backorder = self.picking1.backorder_ids
        # partially process the shipping
        self.shipping1.move_line_ids[0].qty_done = 1
        # validate the shipping
        self.shipping1.with_context(
            skip_immediate=True, skip_backorder=True
        ).button_validate()
        # at this stage we have a backorder shipping with a move with 2 origins
        # the first origin is the processed picking and the second origin is the
        # picking to do to complete the backorder delivery
        backorder = self.shipping1.backorder_ids
        self.assertEqual(len(backorder), 1)
        self.assertEqual(len(backorder.move_ids), 1)
        self.assertEqual(len(backorder.move_ids.move_orig_ids), 2)
        # unrelease the backorder
        backorder.unrelease()
        # we should have 1 move into the picking1 backorder canceled
        self.assertEqual(
            len(picking1_backorder.move_ids.filtered(lambda m: m.state == "cancel")), 1
        )

    def test_simulate_cancel_so(self):
        """Simulate a sale order cancelation.

        action_cancel is called on all related pickings not set to done.
        """
        self.shipping1.action_cancel()
        self.assertEqual(self.shipping1.state, "cancel")
        move_active = self.picking1.move_ids.filtered(lambda l: l.state == "assigned")
        move_cancel = self.picking1.move_ids.filtered(lambda l: l.state == "cancel")
        self.assertEqual(move_active.product_uom_qty, 3.0)
        self.assertEqual(move_cancel.product_uom_qty, 2.0)
        self.assertEqual(move_active.move_dest_ids, self.shipping2.move_ids)
