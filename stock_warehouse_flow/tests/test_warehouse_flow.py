# Copyright 2022 Camptocamp SA
# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.exceptions import UserError

from . import common


class TestWarehouseFlow(common.CommonFlow):
    def test_flow_search_after_applied(self):
        flow_ship_only = self._get_flow("ship_only")
        flow_pick_ship = self._get_flow("pick_ship")
        moves_before = self.env["stock.move"].search([])
        self._run_procurement(self.product, 10, flow_pick_ship.carrier_ids)
        moves = self.env["stock.move"].search([("id", "not in", moves_before.ids)])
        move_ship = moves.filtered(lambda m: m.picking_type_id.code == "outgoing")
        # When flow was applied to move, picking type set by odoo was saved
        # in default_picking_type_id, and flow.to_picking_type_id is set
        self.assertEqual(move_ship.picking_type_id, flow_pick_ship.to_picking_type_id)
        default_type = self.env.ref("stock.picking_type_out")
        self.assertEqual(move_ship.default_picking_type_id, default_type)
        # Only pick_ship matches, because there's a constraint on the carrier
        matching_flows = self.env["stock.warehouse.flow"]._search_for_move(move_ship)
        self.assertEqual(matching_flows, flow_pick_ship)
        # Drop the carrier from the procurement, only ship only flow should match
        move_ship.group_id.carrier_id = False
        matching_flows = self.env["stock.warehouse.flow"]._search_for_move(move_ship)
        self.assertEqual(matching_flows, flow_ship_only)
        # Drop default_picking_type_id, no flow is found, because
        # now flow has Delivery Orders POST as from_picking_type_id
        move_ship.default_picking_type_id = False
        matching_flows = self.env["stock.warehouse.flow"]._search_for_move(move_ship)
        self.assertFalse(matching_flows)

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

    def test_disable_flow_at_move_confirm(self):
        flow = self._get_flow("pick_ship")
        # It is False by default
        flow.impacted_route_ids.apply_flow_on = False
        moves_before = self.env["stock.move"].search([])
        self._run_procurement(self.product, 10, flow.carrier_ids)
        moves = self.env["stock.move"].search([("id", "not in", moves_before.ids)])
        move_ship = moves.filtered(lambda m: m.picking_type_id.code == "outgoing")
        # ensure new move doesn't have flow.to_picking_type_id as picking type
        self.assertNotEqual(move_ship.picking_type_id, flow.to_picking_type_id)

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

    def test_flow_qty_uom_constraint(self):
        flow = self._get_flow("pick_ship")
        flow.write({"qty": 0, "uom_id": False})
        with self.assertRaises(UserError):
            flow.write({"qty": 2})

    def test_split(self):
        self._prepare_split_test()
        moves = self._run_split_flow()
        self.assertEqual(moves.mapped("product_qty"), [4, 1, 4])
        self.assertEqual(
            moves.mapped("picking_type_id.code"), ["outgoing", "outgoing", "internal"]
        )

    def test_nothing_to_split(self):
        self._prepare_split_test()
        moves = self._run_split_flow(4)
        self.assertEqual(moves.mapped("product_qty"), [4, 4])
        self.assertEqual(moves.mapped("picking_type_id.code"), ["outgoing", "internal"])

    def test_split_no_qty_match(self):
        ship_flow, pick_flow = self._prepare_split_test(5)
        ship_flow.unlink()
        with self.assertRaises(UserError):
            self._run_split_flow(4)

    def test_split_no_flow_for_split_move(self):
        ship_flow, pick_flow = self._prepare_split_test()
        ship_flow.unlink()
        with self.assertRaises(UserError):
            self._run_split_flow()
