# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from datetime import datetime

from .common import PromiseReleaseCommonCase


class TestAvailableToPromiseRelease3steps(PromiseReleaseCommonCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.wh.delivery_steps = "pick_pack_ship"

        delivery_pick_rule = cls.wh.delivery_route_id.rule_ids.filtered(
            lambda r: r.location_src_id == cls.loc_stock
        )
        delivery_pick_rule.group_propagation_option = "fixed"

        cls.pc1 = cls._create_picking_chain(
            cls.wh, [(cls.product1, 2)], date=datetime(2019, 9, 2, 16, 0)
        )
        cls.ship1 = cls._out_picking(cls.pc1)
        cls.pack1 = cls._prev_picking(cls.ship1)
        cls.pick1 = cls._prev_picking(cls.pack1)

        cls.pc2 = cls._create_picking_chain(
            cls.wh, [(cls.product1, 3)], date=datetime(2019, 9, 2, 16, 0)
        )
        cls.ship2 = cls._out_picking(cls.pc2)
        cls.pack2 = cls._prev_picking(cls.ship2)
        cls.pick2 = cls._prev_picking(cls.pack2)

        cls._update_qty_in_location(cls.loc_bin1, cls.product1, 15.0)
        cls.wh.delivery_route_id.write(
            {
                "available_to_promise_defer_pull": True,
            }
        )
        (cls.ship1 | cls.ship2).release_available_to_promise()
        assert cls.pick1 == cls.pick2
        cls.pick1.action_assign()

    def test_unrelease_delivery_no_picking_done(self):
        # Not the case with stock_group_by_partner_by_carrier
        # self.assertEqual(self.pick1.move_ids.move_line_ids.product_uom_qty, 5)
        self.assertEqual(
            self.pick1.move_ids.move_dest_ids,
            self.pack1.move_ids | self.pack2.move_ids,
        )
        self.ship1.unrelease()
        self.assertEqual(self.pack1.state, "cancel")
        self.assertTrue(self.ship1.need_release)
        self.assertFalse(self.ship2.need_release)
        # Check pick has one move cancel and one still assign
        move_active = self.pick1.move_ids.filtered(lambda l: l.state == "assigned")
        move_cancel = self.pick1.move_ids.filtered(lambda l: l.state == "cancel")
        # Check the move chain
        self.assertEqual(self.pack1.state, "cancel")
        self.assertEqual(self.pack2.state, "waiting")
        # Active move only for pack2
        self.assertEqual(move_active.move_dest_ids, self.pack2.move_ids)
        # The destination move is on pack2 which is wrong, but it is canceled, so
        # self.assertFalse(move_cancel.move_dest_ids)
        self.assertFalse(move_cancel.move_orig_ids)
        self.assertEqual(self.ship2.move_ids.move_orig_ids, self.pack2.move_ids)
