# Copyright 2025 Camptocamp SA
# Copyright 2025 Raumschmiede GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from datetime import datetime

from .common import PromiseReleaseCommonCase


class TestAvailableToPromiseReleaseCancel(PromiseReleaseCommonCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.wh.delivery_steps = "pick_pack_ship"
        cls._update_qty_in_location(cls.loc_bin1, cls.product1, 50.0)
        cls._update_qty_in_location(cls.loc_bin1, cls.product2, 50.0)

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

        cls.demo_user = cls.env.ref("base.user_demo")
        cls.ship_picking.user_id = cls.demo_user
        cls.pack_picking.user_id = cls.demo_user
        cls.pick_picking.user_id = cls.demo_user

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
        self.assertEqual(self.pick_picking.user_id, self.demo_user)
        self.assertFalse(cancel_picking.user_id)
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
        self.assertEqual(self.pack_picking.user_id, self.demo_user)
        self.assertFalse(cancel_picking.user_id)
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
        self.assertFalse(cancel_picking.user_id)
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
        self.assertFalse(cancel_pickings.user_id)
        self.assertEqual(len(cancel_pickings), 2)
        # In the end, we cancelled 5 units for the pack backorder, returned
        # 5 units from pack -> stock, and 5 units from output -> stock
        pack_cancel = cancel_pickings.filtered(lambda p: p.location_id == self.loc_pack)
        ship_cancel = cancel_pickings.filtered(
            lambda p: p.location_id == self.loc_output
        )
        self.assertEqual(pack_cancel.move_lines.product_uom_qty, 5.0)
        self.assertEqual(ship_cancel.move_lines.product_uom_qty, 5.0)

    @classmethod
    def put_in_pack(cls, move):
        # is it necessary to create stock moves?
        move._action_assign()
        pack = cls.env["stock.quant.package"].create({"name": move.name})
        move.move_line_ids.result_package_id = pack
        return pack

    def test_unrelease_multiple_moves_same_product(self):
        # Create a picking with twice the same move
        product_qty = [
            (self.product1, 20),
        ]
        picking_chain = self._create_picking_chain(self.wh, products=product_qty)
        ship_picking = self._out_picking(picking_chain)
        ship_picking.release_available_to_promise()
        # Creating a second move. Both moves thave the same origin (pack.move_line)
        self.env["stock.move"].create(ship_picking.move_lines._split(4))
        pack_picking = self._prev_picking(ship_picking)
        pick_picking = self._prev_picking(pack_picking)
        self._deliver(pick_picking)
        self._deliver(pack_picking)
        ship_picking.unrelease()
        cancel_pickings = self._get_cleanup_picking()
        self.assertEqual(cancel_pickings.move_lines.product_qty, 20)

    def test_unrelease_packed_multi(self):
        # Pick and pack 2 pickings, unrelease both before shipping
        # Both have same picking types, goods should be returned
        # to stock in the same picking
        ship_no_pack = self.ship_picking
        pack_no_pack = self.pack_picking
        pick_no_pack = self.pick_picking
        # The new picking chain will have packages
        product_qty = [(self.product1, 10), (self.product2, 10)]
        picking_chain = self._create_picking_chain(self.wh, products=product_qty)
        ship_with_pack = self._out_picking(picking_chain)
        ship_with_pack.release_available_to_promise()
        pack_with_pack = self._prev_picking(ship_with_pack)
        pick_with_pack = self._prev_picking(pack_with_pack)
        # Process pick pickings
        self._deliver(pick_with_pack)
        self._deliver(pick_no_pack)
        # put pack moves in packages on pack_with_pack,
        pack_moves = pack_with_pack.move_lines
        pack_move1 = pack_moves.filtered(lambda m: m.product_id == self.product1)
        pack_move2 = pack_moves.filtered(lambda m: m.product_id == self.product2)
        self.put_in_pack(pack_move1)
        self.put_in_pack(pack_move2)
        # Process pack pickings
        self._deliver(pack_with_pack)
        self._deliver(pack_no_pack)
        # unrelease both ship pickings at once
        (ship_with_pack | ship_no_pack).unrelease()
        cancel_pickings = self._get_cleanup_picking()
        # We should have 1 return picking only
        self.assertEqual(len(cancel_pickings), 1)
        # We should have 3 moves
        cancel_moves = cancel_pickings.move_lines
        self.assertEqual(len(cancel_moves), 3)
        # We should have:
        # - 1 move for product1 without pack
        # - 1 move for product1 with pack
        # - 1 move for product2 with pack
        cancel_move1_no_pack = cancel_moves.filtered(
            lambda m: m.product_id == self.product1 and not m.move_line_ids.package_id
        )
        cancel_move1_with_pack = cancel_moves.filtered(
            lambda m: m.product_id == self.product1 and m.move_line_ids.package_id
        )
        cancel_move2_with_pack = cancel_moves.filtered(
            lambda m: m.product_id == self.product2 and m.move_line_ids.package_id
        )
        self.assertTrue(cancel_move1_no_pack)
        self.assertEqual(cancel_move1_no_pack.product_qty, 10)
        self.assertTrue(cancel_move1_with_pack)
        self.assertEqual(cancel_move1_with_pack.product_qty, 10)
        self.assertTrue(cancel_move2_with_pack)
        self.assertEqual(cancel_move2_with_pack.product_qty, 10)

    def test_return_quantity_in_stock(self):
        move_model = self.env["stock.move"]
        pack_move = self.pack_picking.move_lines
        # process pick and pack, so pack is done and returnable
        self._deliver(self.pick_picking)
        self._deliver(self.pack_picking)
        # Using empty_recordsets doesn't raises an exception and doesn't create
        # a return picking
        empty_args = {}
        move_model._return_quantity_in_stock(empty_args)
        self.assertFalse(self._get_cleanup_picking())
        # Adding a move with no quantity
        empty_args = {pack_move.id: 0}
        move_model._return_quantity_in_stock(empty_args)
        self.assertFalse(self._get_cleanup_picking())
        # Adding a quantity should create a return picking
        valid_args = {pack_move.id: 5}
        move_model._return_quantity_in_stock(valid_args)
        return_picking = self._get_cleanup_picking()
        self.assertEqual(return_picking.move_lines.product_qty, 5)

    def test_unrelease_shipped(self):
        self._deliver(self.pick_picking)
        self._deliver(self.pack_picking)
        self._deliver(self.ship_picking)
        self.ship_picking.unrelease()
        # Did nothing
        self.assertEqual(self.ship_picking.state, "done")
        self.assertEqual(self.pack_picking.state, "done")
        self.assertEqual(self.pick_picking.state, "done")
