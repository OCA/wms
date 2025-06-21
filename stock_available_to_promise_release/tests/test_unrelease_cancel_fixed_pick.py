# Copyright 2025 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from datetime import datetime

from .common import PromiseReleaseCommonCase


class TestAvailableToPromiseReleaseCancelFixedPick(PromiseReleaseCommonCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls._update_qty_in_location(cls.loc_bin1, cls.product1, 50.0)
        cls._update_qty_in_location(cls.loc_bin1, cls.product2, 50.0)
        pick_rule = cls.wh.delivery_route_id.rule_ids.filtered(
            lambda r: r.location_src_id == cls.loc_stock
        )
        pick_rule.group_propagation_option = "fixed"
        pick_rule.group_id = cls.env["procurement.group"].create({"name": "Fixed"})
        delivery_route = cls.wh.delivery_route_id
        delivery_route.write(
            {
                "available_to_promise_defer_pull": True,
                "allow_unrelease_return_done_move": True,
            }
        )
        cls.cleanup_type = cls.env["stock.picking.type"].create(
            {
                "name": "Cancel Cleanup",
                "default_location_dest_id": cls.loc_stock.id,
                "sequence_code": "CCP",
                "code": "internal",
            }
        )
        cls.pick_type = pick_rule.picking_type_id
        cls.pick_type.return_picking_type_id = cls.cleanup_type

    def test_full_cancel(self):
        picking_chain1 = self._create_picking_chain(
            self.wh, [(self.product1, 10)], date=datetime(2019, 9, 2, 16, 0)
        )
        picking_chain2 = self._create_picking_chain(
            self.wh, [(self.product1, 10)], date=datetime(2019, 9, 2, 16, 0)
        )
        ship_picking1 = self._out_picking(picking_chain1)
        ship_picking1.release_available_to_promise()
        ship_picking2 = self._out_picking(picking_chain2)
        ship_picking2.release_available_to_promise()
        self.assertNotEqual(ship_picking1, ship_picking2)
        pick1 = self._prev_picking(ship_picking1)
        pick2 = self._prev_picking(ship_picking2)
        self.assertEqual(pick1, pick2)
        self._deliver(pick1)
        self.assertEqual(ship_picking1.state, "assigned")
        self.assertEqual(ship_picking2.state, "assigned")
        ship_picking2.action_cancel()
        self.assertEqual(ship_picking2.state, "cancel")
        self.assertEqual(ship_picking1.state, "assigned")

    def test_partial_cancel(self):
        picking_chain1 = self._create_picking_chain(
            self.wh,
            [(self.product1, 10), (self.product2, 10)],
            date=datetime(2019, 9, 2, 16, 0),
        )
        picking_chain2 = self._create_picking_chain(
            self.wh,
            [(self.product1, 10), (self.product2, 10)],
            date=datetime(2019, 9, 2, 16, 0),
        )
        ship_picking1 = self._out_picking(picking_chain1)
        ship_picking1.release_available_to_promise()
        ship_picking2 = self._out_picking(picking_chain2)
        ship_picking2.release_available_to_promise()
        self.assertNotEqual(ship_picking1, ship_picking2)
        pick1 = self._prev_picking(ship_picking1)
        pick2 = self._prev_picking(ship_picking2)
        self.assertEqual(pick1, pick2)
        self._deliver(pick1)
        self.assertEqual(ship_picking1.state, "assigned")
        self.assertEqual(ship_picking2.state, "assigned")
        ship2_product2_move = ship_picking2.move_ids.filtered(
            lambda m: m.product_id == self.product2
        )
        ship2_product2_move._action_cancel()
        self.assertEqual(ship_picking2.state, "assigned")
        self.assertEqual(ship_picking1.state, "assigned")
