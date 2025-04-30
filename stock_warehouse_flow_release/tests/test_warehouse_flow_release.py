# Copyright 2022 Camptocamp SA
# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.addons.stock_warehouse_flow.tests import common


class TestWarehouseFlowRelease(common.CommonFlow):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Set the default delivery route as pick+ship to make releasing working
        # (there is no need to release a 'ship_only' move)
        cls.wh.delivery_steps = "pick_ship"
        cls.out_rules = cls.env["stock.rule"].search(
            [("picking_type_id.code", "=", "outgoing")]
        )
        cls.out_rules.route_id.available_to_promise_defer_pull = True
        cls.out_rules.route_id.apply_flow_on = "on_release"

    def test_flow_pick_ship_flow_at_confirm(self):
        self.out_rules.route_id.apply_flow_on = "on_confirm"
        # enable flow assigning at confirm
        flow = self._get_flow("pick_ship")
        to_picking_type = flow.to_picking_type_id
        # NOTE: use the recorder when migrating to 15.0 to catch created moves
        moves_before = self.env["stock.move"].search([])
        self._run_procurement(self.product, 10, flow.carrier_ids)
        moves_after = self.env["stock.move"].search([])
        move = moves_after - moves_before
        self.assertEqual(len(move), 1)
        self.assertTrue(move.need_release)
        self.assertEqual(move.picking_type_id, to_picking_type)

    def test_flow_pick_ship_on_release(self):
        """Replace the initial 'ship_only' move by pick+ship chained moves.

        If the delivery route has been configured with the 'Release based on
        Available to Promise' option, the picking type update will occur when
        releasing the move instead of confirming it.
        """
        flow = self._get_flow("pick_ship")
        to_picking_type = flow.to_picking_type_id
        # NOTE: use the recorder when migrating to 15.0 to catch created moves
        moves_before = self.env["stock.move"].search([])
        self._run_procurement(self.product, 10, flow.carrier_ids)
        moves_after = self.env["stock.move"].search([])
        move = moves_after - moves_before
        # Check we got only one move (to release)
        self.assertEqual(len(move), 1)
        self.assertTrue(move.need_release)
        self.assertNotEqual(move.picking_type_id, to_picking_type)
        # Now when releasing this move, the picking type update is happening
        # (and will create chained moves if any as well)
        picking = move.picking_id
        move.picking_id.release_available_to_promise()
        self.assertNotEqual(move.picking_id, picking)
        self.assertTrue(move.picking_id)
        # Check we got pick+ship moves instead of one ship_only move
        move_ship = move
        self.assertRecordValues(
            move_ship,
            [
                {
                    "picking_type_id": to_picking_type.id,
                    "location_id": to_picking_type.default_location_src_id.id,
                    "location_dest_id": self.loc_customer.id,
                },
            ],
        )
        move_pick = move_ship.move_orig_ids
        self.assertTrue(move_pick)
        move_pick.picking_id.action_assign()
        self.assertEqual(move_pick.state, "assigned")
        self._validate_picking(move_pick.picking_id)
        self.assertEqual(move_pick.state, "done")
        self.assertEqual(move_ship.state, "assigned")
        self._validate_picking(move_ship.picking_id)

    def test_flow_split_release(self):
        pick_flow = self._get_flow("pick_ship")
        ship_flow = self._get_flow("ship_only")
        flows = pick_flow | ship_flow
        self._prepare_split_test()
        move = self._run_split_flow()
        self.assertEqual(len(move), 1)
        self.assertTrue(move.need_release)
        self.assertTrue(move.picking_type_id not in flows.to_picking_type_id)
        moves_before = self.env["stock.move"].search([])
        move.picking_id.release_available_to_promise()
        moves_after = self.env["stock.move"].search([])
        moves = moves_after - moves_before
        moves = move | moves
        self.assertEqual(moves.mapped("product_qty"), [4, 1, 4])
        self.assertEqual(
            moves.mapped("picking_type_id.code"), ["outgoing", "outgoing", "internal"]
        )
