# Copyright 2024 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from datetime import timedelta

from odoo import fields

from odoo.addons.stock_release_channel.tests.common import ChannelReleaseCase


class TestChannelComputedFields(ChannelReleaseCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product1.weight = 1
        cls.product2.weight = 3
        cls.channel.picking_ids.move_ids._cal_move_weight()
        cls.channel.picking_ids._cal_weight()
        cls.channel.picking_ids._compute_shipping_weight()

    def assertWeight(self, suffix, product_qties):
        weight = sum([product.weight * qty for product, qty in product_qties])
        for prefix in ["weight_picking", "weight_move"]:
            field = f"{prefix}_{suffix}"
            value = getattr(self.channel, field)
            self.assertEqual(
                weight,
                value,
                f"The value of {field} is {value} and not like expected {weight}",
            )

    def assertWeightFullProgress(self):
        self.assertEqual(
            self.channel.weight_picking_full_progress,
            sum(
                [
                    self.channel.weight_picking_release_ready,
                    self.channel.weight_picking_released,
                    self.channel.weight_picking_done,
                ]
            ),
        )

    def test_computed_fields_counts_not_ready(self):
        self.assertWeight("all", [(self.product1, 5 * 3), (self.product2, 5 * 3)])
        self.assertWeight("release_ready", [])
        self.assertWeight("released", [])
        self.assertWeight("assigned", [])
        self.assertWeight("waiting", [])
        self.assertWeight("late", [])
        self.assertWeight("priority", [])
        self.assertWeight("done", [])
        self.assertWeightFullProgress()

    def test_computed_fields_counts_release_ready(self):
        self._update_qty_in_location(self.loc_bin1, self.product1, 20.0)
        self._update_qty_in_location(self.loc_bin1, self.product2, 20.0)

        self.assertWeight("all", [(self.product1, 5 * 3), (self.product2, 5 * 3)])
        self.assertWeight(
            "release_ready", [(self.product1, 5 * 3), (self.product2, 5 * 3)]
        )
        self.assertWeight("released", [])
        self.assertWeight("assigned", [])
        self.assertWeight("waiting", [])
        self.assertWeight("late", [])
        self.assertWeight("priority", [])
        self.assertWeight("done", [])
        self.assertWeightFullProgress()

    def test_computed_fields_counts_released(self):
        self._update_qty_in_location(self.loc_bin1, self.product1, 20.0)
        self._update_qty_in_location(self.loc_bin1, self.product2, 20.0)
        self.picking.release_available_to_promise()

        self.assertWeight("all", [(self.product1, 5 * 3), (self.product2, 5 * 3)])
        self.assertWeight(
            "release_ready", [(self.product1, 5 * 2), (self.product2, 5 * 2)]
        )
        self.assertWeight("released", [(self.product1, 5), (self.product2, 5)])
        self.assertWeight("assigned", [])
        self.assertWeight("waiting", [(self.product1, 5), (self.product2, 5)])
        self.assertWeight("late", [])
        self.assertWeight("priority", [])
        self.assertWeight("done", [])
        self.assertWeightFullProgress()

    def test_computed_fields_counts_late(self):
        self._update_qty_in_location(self.loc_bin1, self.product1, 20.0)
        self._update_qty_in_location(self.loc_bin1, self.product2, 20.0)
        self.picking.release_available_to_promise()
        # FIXME late should measure late internal operations, not late deliveries
        # pick_picking = self.picking.move_ids.move_orig_ids.picking_id
        # pick_picking.scheduled_date = fields.Datetime.now() - timedelta(hours=1)
        self.picking.scheduled_date = fields.Datetime.now() - timedelta(hours=1)

        self.assertWeight("all", [(self.product1, 5 * 3), (self.product2, 5 * 3)])
        self.assertWeight(
            "release_ready", [(self.product1, 5 * 2), (self.product2, 5 * 2)]
        )
        self.assertWeight("released", [(self.product1, 5), (self.product2, 5)])
        self.assertWeight("assigned", [])
        self.assertWeight("waiting", [(self.product1, 5), (self.product2, 5)])
        self.assertWeight("late", [(self.product1, 5), (self.product2, 5)])
        self.assertWeight("priority", [])
        self.assertWeight("done", [])
        self.assertWeightFullProgress()

    def test_computed_fields_counts_pick_done(self):
        self._update_qty_in_location(self.loc_bin1, self.product1, 20.0)
        self._update_qty_in_location(self.loc_bin1, self.product2, 20.0)
        self.picking.release_available_to_promise()
        pick_picking = self.picking.move_ids.move_orig_ids.picking_id
        self._action_done_picking(pick_picking)

        self.assertWeight("all", [(self.product1, 5 * 3), (self.product2, 5 * 3)])
        self.assertWeight(
            "release_ready", [(self.product1, 5 * 2), (self.product2, 5 * 2)]
        )
        self.assertWeight("released", [(self.product1, 5), (self.product2, 5)])
        self.assertWeight("assigned", [(self.product1, 5), (self.product2, 5)])
        self.assertWeight("waiting", [])
        self.assertWeight("late", [])
        self.assertWeight("priority", [])
        self.assertWeight("done", [])
        self.assertWeightFullProgress()

    def test_computed_fields_counts_ship_done(self):
        self._update_qty_in_location(self.loc_bin1, self.product1, 20.0)
        self._update_qty_in_location(self.loc_bin1, self.product2, 20.0)
        self.picking.release_available_to_promise()
        pick_picking = self.picking.move_ids.move_orig_ids.picking_id
        self._action_done_picking(pick_picking)
        self._action_done_picking(self.picking)

        self.assertWeight("all", [(self.product1, 5 * 3), (self.product2, 5 * 3)])
        self.assertWeight(
            "release_ready", [(self.product1, 5 * 2), (self.product2, 5 * 2)]
        )
        self.assertWeight("released", [])
        self.assertWeight("assigned", [])
        self.assertWeight("waiting", [])
        self.assertWeight("late", [])
        self.assertWeight("priority", [])
        self.assertWeight("done", [(self.product1, 5), (self.product2, 5)])
        self.assertWeightFullProgress()
