# Copyright 2025 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from datetime import datetime

from .common import PromiseReleaseCommonCase


class TestAvailableToPromiseReleaseCancel(PromiseReleaseCommonCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.wh.delivery_steps = "pick_pack_ship"
        cls._update_qty_in_location(cls.loc_bin1, cls.product1, 15.0)

        delivery_route = cls.wh.delivery_route_id
        ship_rule = delivery_route.rule_ids.filtered(
            lambda r: r.location_id == cls.loc_customer
        )
        cls.loc_output = ship_rule.location_src_id
        pack_rule = delivery_route.rule_ids.filtered(
            lambda r: r.location_id == cls.loc_output
        )
        cls.loc_pack = pack_rule.location_src_id
        pick_rule = delivery_route.rule_ids.filtered(
            lambda r: r.location_id == cls.loc_pack
        )
        cls.pick_type = pick_rule.picking_type_id
        cls.pack_type = pack_rule.picking_type_id

        cls.picking_chain = cls._create_picking_chain(
            cls.wh, [(cls.product1, 10)], date=datetime(2019, 9, 2, 16, 0)
        )
        cls.ship_picking = cls._out_picking(cls.picking_chain)
        cls.pack_picking = cls._prev_picking(cls.ship_picking)
        cls.pick_picking = cls._prev_picking(cls.pack_picking)

        # Why is this not working when creating picking after enabling this setting?
        delivery_route.write(
            {
                "available_to_promise_defer_pull": True,
                "allow_unrelease_return_done_move": True,
            }
        )
        cls.ship_picking.release_available_to_promise()
        cls.cleanup_type = cls.env["stock.picking.type"].create(
            {
                "name": "Cancel Cleanup",
                "default_location_dest_id": cls.loc_stock.id,
                "sequence_code": "CCP",
                "code": "internal",
            }
        )
        cls.pick_type.return_picking_type_id = cls.cleanup_type
        cls.pack_type.return_picking_type_id = cls.cleanup_type

    @classmethod
    def _get_cleanup_picking(cls):
        return cls.env["stock.picking"].search(
            [("picking_type_id", "=", cls.cleanup_type.id)]
        )

    def test_unrelease_picked(self):
        # In this case, we should get 1 return picking from
        # WH/PACK to WH/STOCK
        self._deliver(self.pick_picking)
        self.ship_picking.unrelease()
        self.assertTrue(self.ship_picking.need_release)
        self.assertEqual(self.pack_picking.state, "cancel")
        self.assertEqual(self.pick_picking.state, "done")
        cancel_picking = self._get_cleanup_picking()
        self.assertEqual(len(cancel_picking), 1)
        self.assertEqual(cancel_picking.location_id, self.loc_pack)
        self.assertEqual(cancel_picking.location_dest_id, self.loc_stock)

    def test_unrelease_packed(self):
        # In this case, we should get 1 return picking from
        # WH/OUT to WH/STOCK
        self._deliver(self.pick_picking)
        self._deliver(self.pack_picking)
        self.ship_picking.unrelease()
        self.assertTrue(self.ship_picking.need_release)
        self.assertEqual(self.pack_picking.state, "done")
        self.assertEqual(self.pick_picking.state, "done")
        cancel_picking = self._get_cleanup_picking()
        self.assertEqual(len(cancel_picking), 1)
        self.assertEqual(cancel_picking.location_id, self.loc_output)
        self.assertEqual(cancel_picking.location_dest_id, self.loc_stock)

    def test_unrelease_picked_partial(self):
        qty_picked = [(self.product1, 5.0)]
        self._deliver(self.pick_picking, product_qty=qty_picked)
        pick_backorder = self._get_backorder_for_pickings(self.pick_picking)
        self.assertTrue(pick_backorder)
        self.ship_picking.unrelease()
        self.assertTrue(self.ship_picking.need_release)
        self.assertEqual(self.pack_picking.state, "cancel")
        self.assertEqual(self.pick_picking.state, "done")
        cancel_picking = self._get_cleanup_picking()
        # In the end, we cancelled 5 units for the pick backorder, and returned
        # 5 units from pack -> stock
        self.assertEqual(pick_backorder.state, "cancel")
        self.assertEqual(cancel_picking.location_id, self.loc_pack)
        self.assertEqual(cancel_picking.location_dest_id, self.loc_stock)
        self.assertEqual(cancel_picking.move_lines.product_uom_qty, 5.0)

    def test_unrelease_packed_partial(self):
        self._deliver(self.pick_picking)
        qty_packed = [(self.product1, 5.0)]
        self._deliver(self.pack_picking, product_qty=qty_packed)
        pack_backorder = self._get_backorder_for_pickings(self.pack_picking)
        self.assertTrue(pack_backorder)
        self.ship_picking.unrelease()
        self.assertTrue(self.ship_picking.need_release)
        self.assertEqual(self.pack_picking.state, "done")
        self.assertEqual(self.pick_picking.state, "done")
        cancel_pickings = self._get_cleanup_picking()
        self.assertEqual(len(cancel_pickings), 2)
        # In the end, we cancelled 5 units for the pack backorder, returned
        # 5 units from pack -> stock, and 5 units from output -> stock
        pack_cancel = cancel_pickings.filtered(lambda p: p.location_id == self.loc_pack)
        ship_cancel = cancel_pickings.filtered(
            lambda p: p.location_id == self.loc_output
        )
        self.assertEqual(pack_cancel.move_lines.product_uom_qty, 5.0)
        self.assertEqual(ship_cancel.move_lines.product_uom_qty, 5.0)

    def test_unrelease_shipped(self):
        self._deliver(self.pick_picking)
        self._deliver(self.pack_picking)
        self._deliver(self.ship_picking)
        self.ship_picking.unrelease()
        # Did nothing
        self.assertEqual(self.ship_picking.state, "done")
        self.assertEqual(self.pack_picking.state, "done")
        self.assertEqual(self.pick_picking.state, "done")
