# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
# Copyright 2024 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from datetime import timedelta

from odoo import fields

from odoo.addons.stock_release_channel.tests.common import ChannelReleaseCase


class TestChannelComputedFields(ChannelReleaseCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product1.volume = 1
        cls.product2.volume = 3
        cls.channel.picking_ids.move_ids._compute_volume()
        cls.channel.picking_ids._compute_volume()

    def assertVolume(self, suffix, product_qties):
        volume = sum([product.volume * qty for product, qty in product_qties])
        for prefix in ["volume_picking", "volume_move"]:
            field = f"{prefix}_{suffix}"
            value = getattr(self.channel, field)
            self.assertEqual(
                volume,
                value,
                f"The value of {field} is {value} and not like expected {volume}",
            )

    def assertVolumeFullProgress(self):
        self.assertEqual(
            self.channel.volume_picking_full_progress,
            sum(
                [
                    self.channel.volume_picking_release_ready,
                    self.channel.volume_picking_released,
                    self.channel.volume_picking_done,
                ]
            ),
        )

    def test_computed_fields_counts_not_ready(self):
        self.assertVolume("all", [(self.product1, 5 * 3), (self.product2, 5 * 3)])
        self.assertVolume("release_ready", [])
        self.assertVolume("released", [])
        self.assertVolume("assigned", [])
        self.assertVolume("waiting", [])
        self.assertVolume("late", [])
        self.assertVolume("priority", [])
        self.assertVolume("done", [])
        self.assertVolumeFullProgress()

    def test_computed_fields_counts_release_ready(self):
        self._update_qty_in_location(self.loc_bin1, self.product1, 20.0)
        self._update_qty_in_location(self.loc_bin1, self.product2, 20.0)

        self.assertVolume("all", [(self.product1, 5 * 3), (self.product2, 5 * 3)])
        self.assertVolume(
            "release_ready", [(self.product1, 5 * 3), (self.product2, 5 * 3)]
        )
        self.assertVolume("released", [])
        self.assertVolume("assigned", [])
        self.assertVolume("waiting", [])
        self.assertVolume("late", [])
        self.assertVolume("priority", [])
        self.assertVolume("done", [])
        self.assertVolumeFullProgress()

    def test_computed_fields_counts_released(self):
        self._update_qty_in_location(self.loc_bin1, self.product1, 20.0)
        self._update_qty_in_location(self.loc_bin1, self.product2, 20.0)
        self.picking.release_available_to_promise()

        self.assertVolume("all", [(self.product1, 5 * 3), (self.product2, 5 * 3)])
        self.assertVolume(
            "release_ready", [(self.product1, 5 * 2), (self.product2, 5 * 2)]
        )
        self.assertVolume("released", [(self.product1, 5), (self.product2, 5)])
        self.assertVolume("assigned", [])
        self.assertVolume("waiting", [(self.product1, 5), (self.product2, 5)])
        self.assertVolume("late", [])
        self.assertVolume("priority", [])
        self.assertVolume("done", [])
        self.assertVolumeFullProgress()

    def test_computed_fields_counts_late(self):
        self._update_qty_in_location(self.loc_bin1, self.product1, 20.0)
        self._update_qty_in_location(self.loc_bin1, self.product2, 20.0)
        self.picking.release_available_to_promise()
        # FIXME late should measure late internal operations, not late deliveries
        # pick_picking = self.picking.move_ids.move_orig_ids.picking_id
        # pick_picking.scheduled_date = fields.Datetime.now() - timedelta(hours=1)
        self.picking.scheduled_date = fields.Datetime.now() - timedelta(hours=1)

        self.assertVolume("all", [(self.product1, 5 * 3), (self.product2, 5 * 3)])
        self.assertVolume(
            "release_ready", [(self.product1, 5 * 2), (self.product2, 5 * 2)]
        )
        self.assertVolume("released", [(self.product1, 5), (self.product2, 5)])
        self.assertVolume("assigned", [])
        self.assertVolume("waiting", [(self.product1, 5), (self.product2, 5)])
        self.assertVolume("late", [(self.product1, 5), (self.product2, 5)])
        self.assertVolume("priority", [])
        self.assertVolume("done", [])
        self.assertVolumeFullProgress()

    def test_computed_fields_counts_pick_done(self):
        self._update_qty_in_location(self.loc_bin1, self.product1, 20.0)
        self._update_qty_in_location(self.loc_bin1, self.product2, 20.0)
        self.picking.release_available_to_promise()
        pick_picking = self.picking.move_ids.move_orig_ids.picking_id
        self._action_done_picking(pick_picking)

        self.assertVolume("all", [(self.product1, 5 * 3), (self.product2, 5 * 3)])
        self.assertVolume(
            "release_ready", [(self.product1, 5 * 2), (self.product2, 5 * 2)]
        )
        self.assertVolume("released", [(self.product1, 5), (self.product2, 5)])
        self.assertVolume("assigned", [(self.product1, 5), (self.product2, 5)])
        self.assertVolume("waiting", [])
        self.assertVolume("late", [])
        self.assertVolume("priority", [])
        self.assertVolume("done", [])
        self.assertVolumeFullProgress()

    def test_computed_fields_counts_ship_done(self):
        self._update_qty_in_location(self.loc_bin1, self.product1, 20.0)
        self._update_qty_in_location(self.loc_bin1, self.product2, 20.0)
        self.picking.release_available_to_promise()
        pick_picking = self.picking.move_ids.move_orig_ids.picking_id
        self._action_done_picking(pick_picking)
        self._action_done_picking(self.picking)

        self.assertVolume("all", [(self.product1, 5 * 3), (self.product2, 5 * 3)])
        self.assertVolume(
            "release_ready", [(self.product1, 5 * 2), (self.product2, 5 * 2)]
        )
        self.assertVolume("released", [])
        self.assertVolume("assigned", [])
        self.assertVolume("waiting", [])
        self.assertVolume("late", [])
        self.assertVolume("priority", [])
        self.assertVolume("done", [(self.product1, 5), (self.product2, 5)])
        self.assertVolumeFullProgress()
