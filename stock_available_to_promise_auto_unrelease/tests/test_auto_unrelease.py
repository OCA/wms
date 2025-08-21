# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from datetime import datetime

from odoo.addons.queue_job.tests.common import trap_jobs
from odoo.addons.stock_available_to_promise_release.tests.common import (
    PromiseReleaseCommonCase,
)


class TestAutoUnrelease(PromiseReleaseCommonCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        delivery_pick_rule = cls.wh.delivery_route_id.rule_ids.filtered(
            lambda r: r.location_src_id == cls.loc_stock
        )
        delivery_pick_rule.group_propagation_option = "fixed"

        cls.pc1 = cls._create_picking_chain(
            cls.wh, [(cls.product1, 2)], date=datetime(2025, 8, 30, 16, 0)
        )
        cls.shipping1 = cls._out_picking(cls.pc1)
        cls.pc2 = cls._create_picking_chain(
            cls.wh, [(cls.product1, 3)], date=datetime(2025, 8, 30, 16, 0)
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

        cls.picking1.picking_type_id.unrelease_on_unavailable_to_promise = True

    @classmethod
    def _make_location_inventory(cls, location, product, quantity: float):
        """Make an inventory for the given product in the given location"""
        inventory_quant = (
            cls.env["stock.quant"]
            .with_context(inventory_mode=True)
            .create(
                {
                    "location_id": location.id,
                    "product_id": product.id,
                    "inventory_quantity": quantity,
                }
            )
        )
        inventory_quant.action_apply_inventory()

    def test_auto_unrelease(self):
        """Test that if qty in source location is no more available to promise,
        the corresponding move is un-released."""
        self.assertFalse(self.shipping1.need_release)
        self.assertFalse(self.shipping2.need_release)
        self.assertEqual(self.picking1.move_ids.state, "assigned")
        self.assertEqual(self.picking2.move_ids.state, "assigned")
        with trap_jobs() as trap:
            # in case of inventory, assigned moves are un assigned if no more
            # product is available to promise
            self._make_location_inventory(self.loc_bin1, self.product1, 0.0)
            trap.assert_jobs_count(2)
            for move in self.deliveries.move_ids:
                # we expect the unrelease each move of each delivery for the
                # related product
                trap.assert_enqueued_job(
                    move._do_unrelease_no_more_available,
                    args=(),
                    kwargs={},
                )

            trap.perform_enqueued_jobs()
        self.assertTrue(self.shipping1.need_release)
        self.assertTrue(self.shipping2.need_release)
        self.assertEqual(self.picking1.state, "cancel")
        self.assertEqual(self.picking2.state, "cancel")
