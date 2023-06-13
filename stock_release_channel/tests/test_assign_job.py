# Copyright 2022 ACSONE SA/NV (http://www.acsone.eu)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)


from odoo.addons.queue_job.tests.common import trap_jobs

from .common import ReleaseChannelCase


class TestReleaseChannel(ReleaseChannelCase):
    def _test_assign_channels(self, expected, message=""):
        move = self._create_single_move(self.product1, 10)
        move.picking_id.priority = "1"
        move2 = self._create_single_move(self.product2, 10)
        with trap_jobs() as trap:
            picking1 = move.picking_id
            picking2 = move2.picking_id
            (picking1 + picking2)._delay_assign_release_channel()
            trap.assert_jobs_count(1, only=picking1.assign_release_channel)
            trap.assert_jobs_count(1, only=picking2.assign_release_channel)
            trap.perform_enqueued_jobs()
            self.assertEqual(f"{message}", trap.enqueued_jobs[0].result)
        self.assertEqual(move.picking_id.release_channel_id, expected)
        self.assertEqual(move2.picking_id.release_channel_id, self.default_channel)

    def test_assign_channel_domain(self):
        channel = self._create_channel(
            name="Test Domain",
            sequence=1,
            rule_domain=[("priority", "=", "1")],
        )
        self._test_assign_channels(channel)

    def test_assign_channel_none_domain(self):
        self.default_channel.action_sleep()
        self.default_channel = self.env["stock.release.channel"].browse()
        self._create_channel(
            name="Test Domain",
            sequence=1,
            rule_domain=[("priority", "=", "1")],
        )
        move = self._create_single_move(self.product1, 10)
        with trap_jobs() as trap:
            picking = move.picking_id
            message = (
                f"Transfer {picking.name} could not be assigned to a "
                "channel, you should add a final catch-all rule\n"
            )
            picking._delay_assign_release_channel()
            trap.assert_jobs_count(1, only=picking.assign_release_channel)
            trap.perform_enqueued_jobs()
            self.assertEqual(message, trap.enqueued_jobs[0].result)
        move = self._create_single_move(self.product2, 10)
        with trap_jobs() as trap:
            picking = move.picking_id
            message = (
                f"Transfer {picking.name} could not be assigned to a "
                "channel, you should add a final catch-all rule\n"
            )
            picking._delay_assign_release_channel()
            trap.assert_jobs_count(1, only=picking.assign_release_channel)
            trap.perform_enqueued_jobs()
            self.assertEqual(message, trap.enqueued_jobs[0].result)
