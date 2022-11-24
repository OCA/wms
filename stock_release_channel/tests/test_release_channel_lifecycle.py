# Copyright 2022 ACSONE SA/NV (http://www.acsone.eu)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
from unittest import mock

from odoo import exceptions

from odoo.addons.queue_job.job import identity_exact
from odoo.addons.queue_job.tests.common import trap_jobs

from .common import ReleaseChannelCase


class TestReleaseChannelLifeCycle(ReleaseChannelCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_release_channel_locked_no_release_next_batch(self):
        self.default_channel.release_next_batch()
        self.default_channel.action_lock()
        with self.assertRaisesRegex(
            exceptions.UserError,
            "The release of pickings is not allowed",
        ):
            self.default_channel.release_next_batch()

    def test_release_channel_asleep_no_release_next_batch(self):
        self.default_channel.release_next_batch()
        self.default_channel.action_sleep()
        with self.assertRaisesRegex(
            exceptions.UserError,
            "The release of pickings is not allowed",
        ):
            self.default_channel.release_next_batch()

    def test_release_channel_asleep_not_assignable(self):
        move = self._create_single_move(self.product1, 10)
        move.picking_id.assign_release_channel()
        self.assertEqual(move.picking_id.release_channel_id, self.default_channel)
        self.default_channel.action_sleep()
        move = self._create_single_move(self.product1, 10)
        move.picking_id.assign_release_channel()
        self.assertFalse(move.picking_id.release_channel_id)

    def test_release_channel_wake_up_assign(self):
        self.default_channel.action_sleep()
        move = self._create_single_move(self.product1, 10)
        move.picking_id.assign_release_channel()
        move.need_release = True
        self.assertFalse(move.picking_id.release_channel_id)
        with trap_jobs() as trap:
            self.default_channel.action_wake_up()
            trap.assert_jobs_count(1)
            trap.assert_enqueued_job(
                move.picking_id.assign_release_channel,
                args=(),
                kwargs={},
                properties=dict(
                    identity_key=identity_exact,
                ),
            )
            trap.enqueued_jobs[0].perform()
        self.assertEqual(move.picking_id.release_channel_id, self.default_channel)

    def test_release_channel_sleep_unassign(self):
        self.move = self._create_single_move(self.product1, 10)
        self.move.picking_id.assign_release_channel()
        self.picking = self.move.picking_id
        self.assertEqual(self.picking.release_channel_id, self.default_channel)
        self.default_channel.action_sleep()
        self.assertFalse(self.picking.release_channel_id)

    def test_release_channel_sleep_unrelease(self):
        self.move = self._create_single_move(self.product1, 10)
        self.move.picking_id.assign_release_channel()
        self.picking = self.move.picking_id
        with mock.patch.object(
            self.picking.__class__,
            "unrelease",
        ) as release_picking:
            self.default_channel.action_sleep()
        self.assertEqual(release_picking.call_count, 1)
