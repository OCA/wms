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
        # self.assertEqual(self.picking1.move_lines.move_line_ids.product_uom_qty, 5)
        self.assertEqual(
            self.picking1.move_lines.move_dest_ids, self.deliveries.move_lines
        )
        self.shipping1.unrelease()
        self.assertEqual(len(self.picking1.move_lines), 2)
        move_cancel = self.picking1.move_lines.filtered(lambda m: m.state == "cancel")
        self.assertEqual(move_cancel.product_uom_qty, 2)
        self.assertTrue(self.shipping1.need_release)
        self.assertTrue(
            all(m.procure_method == "make_to_order" for m in self.shipping1.move_lines)
        )

    # def test_unrelease_picking_is_done(self):
    #     # the pick moves for delivery 1 and 2 are merged
    #     self.assertEqual(self.picking1, self.picking2)
    #     # do the first step
    #     for line in self.picking1.move_line_ids:
    #         line.qty_done = line.product_uom_qty
    #     self.picking1.button_validate()
    #     self.assertEqual(self.picking1.state, "done")
    #     self.shipping1.unrelease()

    def test_simulate_cancel_so(self):
        """Simulate a sale order cancelation.

        action_cancel is called on all related pickings not set to done.
        """
        self.shipping1.action_cancel()
        self.assertEqual(self.shipping1.state, "cancel")
        move_active = self.picking1.move_lines.filtered(lambda l: l.state == "assigned")
        move_cancel = self.picking1.move_lines.filtered(lambda l: l.state == "cancel")
        self.assertEqual(move_active.product_uom_qty, 3.0)
        self.assertEqual(move_cancel.product_uom_qty, 2.0)
        self.assertEqual(move_active.move_dest_ids, self.shipping2.move_lines)
        self.assertTrue(
            all(m.procure_method == "make_to_order" for m in self.shipping2.move_lines)
        )
