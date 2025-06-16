# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from datetime import datetime

from .common import PromiseReleaseCommonCase


class TestMergeMoves(PromiseReleaseCommonCase):
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
        cls._update_qty_in_location(cls.loc_bin1, cls.product1, 15.0)
        cls.wh.delivery_route_id.write(
            {
                "available_to_promise_defer_pull": True,
            }
        )
        cls.shipping1.release_available_to_promise()
        cls.picking1 = cls._prev_picking(cls.shipping1)
        cls.picking1.action_assign()

    @classmethod
    def _out_picking(cls, pickings):
        return pickings.filtered(lambda r: r.picking_type_code == "outgoing")

    @classmethod
    def _prev_picking(cls, picking):
        return picking.move_ids.move_orig_ids.picking_id

    def _procure(self, qty):
        """Create a procurement for a given quantity and run it.

        The created procurement will have the required values required
        to create a move mergeable with the existing ones into the same
        shipment.
        """
        values = {
            "company_id": self.wh.company_id,
            "group_id": self.shipping1.group_id,
            "date_planned": self.shipping1.move_ids[0].date,
            "warehouse_id": self.wh,
        }
        self.env["procurement.group"].run(
            [
                self.env["procurement.group"].Procurement(
                    self.product1,
                    qty,
                    self.product1.uom_id,
                    self.loc_customer,
                    "TEST",
                    "TEST",
                    self.wh.company_id,
                    values,
                )
            ]
        )

    def test_unrelease_at_move_merge(self):
        self.assertFalse(self.shipping1.need_release)
        self.assertEqual(1, len(self.shipping1.move_ids))
        original_qty = self.shipping1.move_ids.product_uom_qty
        # run a new procurement that will create a move in the same shipment
        self._procure(2)
        self.assertEqual(1, len(self.shipping1.move_ids))
        self.assertEqual(original_qty + 2, self.shipping1.move_ids.product_uom_qty)
        self.assertFalse(self.shipping1.need_release)
        # since the shipment is no more released, the picking should be canceled
        self.assertEqual("cancel", self.picking1.state)

    def test_unrelease_at_move_merge_2(self):
        # create a negative quant to cancel teh qty to deliver
        self.assertFalse(self.shipping1.need_release)
        self.assertEqual(1, len(self.shipping1.move_ids))
        original_qty = self.shipping1.move_ids.product_uom_qty
        # run a new procurement that will create a move in the same shipment
        self._procure(-original_qty)
        self.assertEqual(1, len(self.shipping1.move_ids))
        self.assertEqual(0, self.shipping1.move_ids.product_uom_qty)
        # no more qty to deliver, the shipment and picking should be canceled
        self.assertEqual("cancel", self.shipping1.state)
        self.assertEqual("cancel", self.picking1.state)

    def test_unrelease_at_move_merge_merged(self):
        # Create a new shipping for the same product and date
        # This will create a new move that will be merged with the existing one
        # at merge time in the existing picking
        pc2 = self._create_picking_chain(
            self.wh, [(self.product1, 3)], date=datetime(2019, 9, 2, 16, 0)
        )
        shipping2 = self._out_picking(pc2)
        shipping2.release_available_to_promise()
        picking2 = self._prev_picking(shipping2)
        picking2.action_assign()
        self.assertEqual(self.picking1, picking2)
        self.assertEqual(1, len(self.picking1.move_ids))

        original_qty_1 = self.shipping1.move_ids.product_uom_qty
        original_qty_2 = shipping2.move_ids.product_uom_qty

        # pick1 and pick2 are the same
        self.assertEqual(self.picking1, picking2)

        # partially process the picking
        move = self.picking1.move_ids
        move.move_line_ids.quantity = 2
        move.move_line_ids.picked = True
        # run a new procurement for the same product in the shipment 1
        self._procure(2)

        # the move should not be merged with the existing one since
        # the first one is partially processed
        self.assertEqual(2, len(self.shipping1.move_ids))
        self.assertEqual(
            2 + original_qty_1, sum(self.shipping1.move_ids.mapped("product_uom_qty"))
        )
        self.assertTrue(self.shipping1.need_release)

        # the pick should still contain a move with the processed qty
        # and the qty to do should be the one from shipping2
        move = self.picking1.move_ids.filtered(
            lambda m: m.state in ("assigned", "partially_available")
        )
        self.assertEqual(2, move.move_line_ids.quantity)
        self.assertEqual(5, move.product_uom_qty)

        # if we release the ship 1 again, a new move should be created
        # and merged with the existing one
        self.shipping1.release_available_to_promise()
        move = self.picking1.move_ids.filtered(
            lambda m: m.state in ("assigned", "partially_available")
        )
        self.assertEqual(1, len(move))
        self.assertEqual(2 + original_qty_1 + original_qty_2, move.product_uom_qty)
        self.assertEqual(2, move.move_line_ids.quantity)

    def test_default_merge(self):
        # check that the merge is still working when the available_to_promise_defer_pull
        # is False
        self.wh.delivery_route_id.write(
            {
                "available_to_promise_defer_pull": False,
            }
        )
        original_qty = self.shipping1.move_ids.product_uom_qty
        # run a new procurement for the same product in the shipment 1
        self._procure(2)
        self.assertEqual(1, len(self.shipping1.move_ids))
        self.assertEqual(original_qty + 2, self.shipping1.move_ids.product_uom_qty)
