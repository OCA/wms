# Copyright 2022 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from contextlib import contextmanager

from odoo.addons.queue_job.job import identity_exact
from odoo.addons.queue_job.tests.common import trap_jobs
from odoo.addons.stock_release_channel.tests.common import ChannelReleaseCase


class TestChannelReleaseAuto(ChannelReleaseCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.channel.release_mode = "auto"

        cls._update_qty_in_location(cls.loc_bin1, cls.product1, 1000.0)
        cls._update_qty_in_location(cls.loc_bin1, cls.product2, 1000.0)

        # invalidate cache for computed fields bases on qty in stock
        cls.env.invalidate_all()

    @contextmanager
    def assert_release_job_enqueued(self, channel):
        pickings_to_release = channel._get_pickings_to_release()
        self.assertTrue(pickings_to_release)
        with trap_jobs() as trap:
            yield
            trap.assert_jobs_count(len(pickings_to_release))
            for pick in pickings_to_release:
                trap.assert_enqueued_job(
                    pick.auto_release_available_to_promise,
                    args=(),
                    kwargs={},
                    properties=dict(
                        identity_key=identity_exact,
                    ),
                )

    def test_channel_auto_release_forbidden(self):
        self.assertTrue(self.channel.is_auto_release_allowed)
        self.channel.release_forbidden = True
        self.assertFalse(self.channel.is_auto_release_allowed)

    def test_channel_search_is_auto_release_allowed(self):
        self.assertTrue(self.channel.is_auto_release_allowed)
        self.assertIn(
            self.channel,
            self.env["stock.release.channel"].search(
                [("is_auto_release_allowed", "=", True)]
            ),
        )
        self.assertNotIn(
            self.channel,
            self.env["stock.release.channel"].search(
                [("is_auto_release_allowed", "=", False)]
            ),
        )
        self.channel.release_forbidden = True
        self.assertFalse(self.channel.is_auto_release_allowed)
        self.assertNotIn(
            self.channel,
            self.env["stock.release.channel"].search(
                [("is_auto_release_allowed", "=", True)]
            ),
        )
        self.assertIn(
            self.channel,
            self.env["stock.release.channel"].search(
                [("is_auto_release_allowed", "=", False)]
            ),
        )

    def test_picking_auto_release_forbidden(self):
        self.assertTrue(self.picking.is_auto_release_allowed)
        self.channel.release_forbidden = True
        self.assertFalse(self.picking.is_auto_release_allowed)

    def test_picking_search_is_auto_release_allowed(self):
        self.assertTrue(self.picking.is_auto_release_allowed)
        self.assertIn(
            self.picking,
            self.env["stock.picking"].search([("is_auto_release_allowed", "=", True)]),
        )
        self.assertNotIn(
            self.picking,
            self.env["stock.picking"].search([("is_auto_release_allowed", "=", False)]),
        )
        self.channel.release_forbidden = True
        self.assertFalse(self.picking.is_auto_release_allowed)
        self.assertNotIn(
            self.picking,
            self.env["stock.picking"].search([("is_auto_release_allowed", "=", True)]),
        )
        self.assertIn(
            self.picking,
            self.env["stock.picking"].search([("is_auto_release_allowed", "=", False)]),
        )

    def test_channel_auto_release_all_launch_release_job(self):
        with self.assert_release_job_enqueued(self.channel):
            self.channel.auto_release_all()

    def test_picking_assign_release_channel_launch_release_job(self):
        self.picking.release_channel_id = None
        self.channel.release_mode = "batch"
        with trap_jobs() as trap:
            self.picking.assign_release_channel()
            self.assertEqual(self.picking.release_channel_id, self.channel)
            trap.assert_jobs_count(0)
        self.picking.release_channel_id = None
        self.channel.release_mode = "auto"
        with trap_jobs() as trap:
            self.picking.assign_release_channel()
            self.assertEqual(self.picking.release_channel_id, self.channel)
            trap.assert_jobs_count(1)
            trap.assert_enqueued_job(
                self.picking.auto_release_available_to_promise,
                args=(),
                kwargs={},
                properties=dict(
                    identity_key=identity_exact,
                ),
            )

    def test_release_channel_change_mode_launch_release_job(self):
        self.channel.release_mode = "batch"
        with self.assert_release_job_enqueued(self.channel):
            self.channel.release_mode = "auto"

    def test_release_channel_action_unlock_launch_release_job(self):
        self.channel.action_lock()
        with self.assert_release_job_enqueued(self.channel):
            self.channel.action_unlock()
