# Copyright 2020 Camptocamp (https://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
"""
When we "release" moves, we set the "printed" flag on the transfers,
because after a release, we shouldn't have any new move merged in a
"wave" of release.

The stock_available_to_promise_release module adds the flag on all
the transfer chain (pick, pack, ship, ...), but as transfers created
for dynamic routing are created later, we have to ensure that transfers
for these new moves have the flag. These tests check this.
"""

from odoo.addons.stock_available_to_promise_release.tests.common import (
    PromiseReleaseCommonCase,
)


class TestAvailableToPromiseReleaseDynamicRouting(PromiseReleaseCommonCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.location_hb = cls.env["stock.location"].create(
            {"name": "Highbay", "location_id": cls.wh.lot_stock_id.id}
        )
        cls.location_hb_1 = cls.env["stock.location"].create(
            {"name": "Highbay Shelf 1", "location_id": cls.location_hb.id}
        )
        cls.location_handover = cls.env["stock.location"].create(
            {"name": "Handover", "location_id": cls.wh.lot_stock_id.id}
        )

    def test_dynamic_routing_pull_printed(self):
        """Pull Dynamic routing applied after release get "printed" flag"""
        pick_type_routing_op = self.env["stock.picking.type"].create(
            {
                "name": "Dynamic Routing",
                "code": "internal",
                "sequence_code": "WH/HO",
                "warehouse_id": self.wh.id,
                "use_create_lots": False,
                "use_existing_lots": True,
                "default_location_src_id": self.location_hb.id,
                "default_location_dest_id": self.location_handover.id,
            }
        )
        self.env["stock.routing"].create(
            {
                "location_id": self.location_hb.id,
                "picking_type_id": self.wh.pick_type_id.id,
                "rule_ids": [
                    (
                        0,
                        0,
                        {"method": "pull", "picking_type_id": pick_type_routing_op.id},
                    )
                ],
            }
        )
        self.wh.delivery_route_id.write({"available_to_promise_defer_pull": True})

        self._update_qty_in_location(self.location_hb_1, self.product1, 20.0)
        self._update_qty_in_location(self.location_hb_1, self.product2, 10.0)

        pickings = self._create_picking_chain(
            self.wh, [(self.product1, 20), (self.product2, 10)],
        )
        self.assertEqual(len(pickings), 1, "expect only the last out->customer")
        cust_picking = pickings
        self.assertRecordValues(
            cust_picking,
            [
                {
                    "state": "waiting",
                    "location_id": self.wh.wh_output_stock_loc_id.id,
                    "location_dest_id": self.loc_customer.id,
                }
            ],
        )
        cust_picking.release_available_to_promise()

        pick_moves = cust_picking.move_lines.move_orig_ids
        self.assertEqual(len(pick_moves), 2)
        # this picking is created by standard 2-step rules
        pick_picking = pick_moves.picking_id
        # this flag is set by stock_available_to_promise_release
        self.assertTrue(pick_picking.printed)

        routing_moves = pick_moves.move_orig_ids
        # if we put "printed" after we assign the 1st move only, the 2nd
        # move will not be grouped in the same picking
        self.assertEqual(len(routing_moves), 2)
        routing_picking = routing_moves.picking_id
        self.assertEqual(routing_picking.picking_type_id, pick_type_routing_op)

        self.assertTrue(routing_picking.printed)

    def test_dynamic_routing_change_picking_type_printed(self):
        """Type Dynamic routing applied after release get "printed" flag"""
        self.wh.delivery_route_id.write({"available_to_promise_defer_pull": True})

        area1 = self.env["stock.location"].create(
            {"location_id": self.wh.wh_output_stock_loc_id.id, "name": "Area1"}
        )
        pick_loc = self.wh.pick_type_id.default_location_src_id
        pick_type_routing_op = self.env["stock.picking.type"].create(
            {
                "name": "Dynamic Routing",
                "code": "internal",
                "sequence_code": "WH/PICK2",
                "warehouse_id": self.wh.id,
                "use_create_lots": False,
                "use_existing_lots": True,
                "default_location_src_id": pick_loc.id,
                "default_location_dest_id": area1.id,
            }
        )
        self.env["stock.routing"].create(
            {
                "location_id": pick_loc.id,
                "picking_type_id": self.wh.pick_type_id.id,
                "rule_ids": [
                    (
                        0,
                        0,
                        {"method": "pull", "picking_type_id": pick_type_routing_op.id},
                    )
                ],
            }
        )

        self._update_qty_in_location(self.loc_bin1, self.product1, 20.0)
        self._update_qty_in_location(self.loc_bin1, self.product2, 10.0)

        pickings = self._create_picking_chain(
            self.wh, [(self.product1, 20), (self.product2, 10)],
        )
        self.assertEqual(len(pickings), 1, "expect only the last out->customer")
        cust_picking = pickings
        self.assertRecordValues(
            cust_picking,
            [
                {
                    "state": "waiting",
                    "location_id": self.wh.wh_output_stock_loc_id.id,
                    "location_dest_id": self.loc_customer.id,
                }
            ],
        )
        cust_picking.release_available_to_promise()

        pick_moves = cust_picking.move_lines.move_orig_ids
        self.assertEqual(len(pick_moves), 2)
        # this picking has been created to change the picking type
        pick_picking = pick_moves.picking_id
        self.assertEqual(pick_picking.picking_type_id, pick_type_routing_op)
        # this flag is set by stock_available_to_promise_release
        self.assertTrue(pick_picking.printed)

    def test_dynamic_routing_change_picking_type_out_printed(self):
        """Type Dynamic routing (on OUT) applied after release get "printed" flag

        Ensure the "printed" flag is set even when we have no "move_dest_ids"
        moves.
        """
        self.wh.delivery_route_id.write({"available_to_promise_defer_pull": True})
        pick_type_routing = self.wh.pick_type_id.copy(
            {"name": "PICKP Routing", "sequence_code": "WH/PICKP"}
        )
        self.env["stock.routing"].create(
            {
                "location_id": pick_type_routing.default_location_src_id.id,
                "picking_type_id": self.wh.pick_type_id.id,
                "rule_ids": [
                    (0, 0, {"method": "pull", "picking_type_id": pick_type_routing.id},)
                ],
            }
        )
        out_type_routing = self.wh.out_type_id.copy(
            {"name": "OUTP Routing", "sequence_code": "WH/OUTP"}
        )
        self.env["stock.routing"].create(
            {
                "location_id": out_type_routing.default_location_src_id.id,
                "picking_type_id": self.wh.out_type_id.id,
                "rule_ids": [
                    (0, 0, {"method": "pull", "picking_type_id": out_type_routing.id})
                ],
            }
        )

        self._update_qty_in_location(self.loc_bin1, self.product1, 20.0)
        self._update_qty_in_location(self.loc_bin1, self.product2, 10.0)

        pickings = self._create_picking_chain(
            self.wh, [(self.product1, 20), (self.product2, 10)],
        )
        self.assertEqual(len(pickings), 1, "expect only the last out->customer")
        cust_picking = pickings
        cust_picking.release_available_to_promise()

        # the original cust_picking has been canceled, because it is replaced
        # by picking with the "OUTP" picking type
        self.assertRecordValues(cust_picking, [{"state": "cancel"}])

        new_cust_picking = self.env["stock.picking"].search(
            [("picking_type_id", "=", out_type_routing.id)]
        )

        self.assertEqual(len(new_cust_picking.move_lines), 2)
        self.assertRecordValues(
            new_cust_picking,
            [
                {
                    "state": "waiting",
                    "location_id": self.wh.wh_output_stock_loc_id.id,
                    "location_dest_id": self.loc_customer.id,
                    "picking_type_id": out_type_routing.id,
                    "printed": True,
                }
            ],
        )
