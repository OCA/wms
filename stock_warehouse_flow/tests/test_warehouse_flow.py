# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.exceptions import UserError

from . import common


class TestWarehouseFlow(common.CommonFlow):
    def test_flow_ship_only(self):
        """Replace the initial move by a 'ship_only' move."""
        # NOTE: use the recorder when migrating to 15.0 to catch created moves
        moves_before = self.env["stock.move"].search([])
        flow = self._get_flow("ship_only")
        self._run_procurement(self.product, 10, flow.carrier_ids)
        moves_after = self.env["stock.move"].search([])
        moves = moves_after - moves_before
        # Check we got pick+ship moves instead of one ship_only move
        move_ship = moves.filtered(lambda m: m.picking_type_id.code == "outgoing")
        to_picking_type = flow.to_picking_type_id
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
        self.assertIn(flow.sequence_prefix, move_ship.picking_id.name)
        move_ship.picking_id.action_assign()
        self.assertEqual(move_ship.state, "assigned")
        self._validate_picking(move_ship.picking_id)

    def test_flow_pick_ship(self):
        """Replace the initial move by pick+ship chained moves."""
        # NOTE: use the recorder when migrating to 15.0 to catch created moves
        moves_before = self.env["stock.move"].search([])
        flow = self._get_flow("pick_ship")
        self._run_procurement(self.product, 10, flow.carrier_ids)
        moves_after = self.env["stock.move"].search([])
        moves = moves_after - moves_before
        # Check we got pick+ship moves instead of one ship_only move
        move_ship = moves.filtered(lambda m: m.picking_type_id.code == "outgoing")
        to_picking_type = flow.to_picking_type_id
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
        self.assertIn(flow.sequence_prefix, move_ship.picking_id.name)
        move_pick = move_ship.move_orig_ids
        self.assertTrue(move_pick)
        move_pick.picking_id.action_assign()
        self.assertEqual(move_pick.state, "assigned")
        self._validate_picking(move_pick.picking_id)
        self.assertEqual(move_pick.state, "done")
        self.assertEqual(move_ship.state, "assigned")
        self._validate_picking(move_ship.picking_id)

    def test_no_rule_found_on_delivery_route(self):
        flow = self._get_flow("pick_ship")
        # Remove the rule
        self.assertFalse(flow.warning)
        rule = flow._get_rule_from_delivery_route()
        rule.unlink()
        # Check the warning message
        self.assertTrue(flow.warning)
        # Check that an error is raised when processing the move
        exception_msg = (
            "No rule corresponding to .*%s.* operation type "
            "has been found on delivery route .*%s.*.\n"
            "Please check your configuration."
        ) % (
            flow.to_picking_type_id.display_name,
            flow.delivery_route_id.display_name,
        )
        with self.assertRaisesRegex(UserError, exception_msg):
            self._run_procurement(self.product, 10, flow.carrier_ids)

    def test_no_valid_flow_for_move(self):
        flow = self._get_flow("ship_only")
        flow.move_domain = "[('state', '=', 'unknown')]"
        message = "^No routing flow available for the move"
        with self.assertRaisesRegex(UserError, message):
            self._run_procurement(self.product, 10, flow.carrier_ids)

    def test_flow_uniq_constraint(self):
        flow = self._get_flow("pick_ship")
        vals = flow.copy_data()[0]
        with self.assertRaises(UserError):
            vals["carrier_ids"] = [
                (6, 0, self.env.ref("delivery.delivery_carrier").ids)
            ]
            self.env["stock.warehouse.flow"].create(vals)
