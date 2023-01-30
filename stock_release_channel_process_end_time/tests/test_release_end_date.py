# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from freezegun import freeze_time

from odoo import fields

from odoo.addons.queue_job.job import Job
from odoo.addons.stock_release_channel.tests.common import ChannelReleaseCase


class ReleaseChannelEndDateCase(ChannelReleaseCase):
    @freeze_time("2023-01-27")
    def test_channel_end_date(self):
        # Set the end time
        self.channel.process_end_time = 23.0
        # Asleep the release channel to void the process end date
        self.channel.action_sleep()
        self.channel.invalidate_recordset()
        # Wake up the channel to set the process end date
        self.channel.action_wake_up()
        self.assertEqual(
            "2023-01-27 23:00:00",
            fields.Datetime.to_string(self.channel.process_end_date),
        )

    @freeze_time("2023-01-27 10:00:00")
    def test_channel_end_date_tomorrow(self):
        # Set the end time
        self.channel.process_end_time = 1.0
        # Asleep the release channel to void the process end date
        self.channel.action_sleep()
        self.channel.invalidate_recordset()
        # Wake up the channel to set the process end date
        # Current time is 10:00:00
        self.channel.action_wake_up()
        self.assertEqual(
            "2023-01-28 01:00:00",
            fields.Datetime.to_string(self.channel.process_end_date),
        )

    @freeze_time("2023-01-27 10:00:00")
    def test_channel_end_date_manual(self):
        # Set the end time
        self.channel.process_end_time = 1.0
        # Asleep the release channel to void the process end date
        self.channel.action_sleep()
        self.channel.invalidate_recordset()
        # Wake up the channel to set the process end date
        # Current time is 10:00:00
        self.channel.action_wake_up()
        self.assertEqual(
            "2023-01-28 01:00:00",
            fields.Datetime.to_string(self.channel.process_end_date),
        )

        # We force the end date
        self.channel.process_end_date = "2023-01-27 23:30:00"
        self.assertEqual(
            "2023-01-27 23:30:00",
            fields.Datetime.to_string(self.channel.process_end_date),
        )

    @freeze_time("2023-01-27 10:00:00")
    def test_picking_scheduled_date(self):
        # Remove existing jobs as some already exists to assign pickings to channel
        jobs_before = self.env["queue.job"].search([])
        jobs_before.unlink()
        # Set the end time
        self.channel.process_end_time = 23.0
        # Asleep the release channel to void the process end date
        self.channel.action_sleep()
        self.channel.invalidate_recordset()
        self.channel.action_wake_up()
        # Execute the picking channel assignations
        jobs_after = self.env["queue.job"].search([])
        for job in jobs_after:
            job = Job.load(job.env, job.uuid)
            job.perform()
        pickings = self.channel.picking_ids
        # Check the scheduled date is corresponding to the one on channel
        for picking in pickings:
            self.assertEqual(
                "2023-01-27 23:00:00", fields.Datetime.to_string(picking.scheduled_date)
            )

    def test_can_edit_time(self):
        user = self.env.ref("base.user_demo")
        group = self.env.ref("stock.group_stock_manager")
        user.groups_id -= group
        self.assertFalse(self.channel.with_user(user).process_end_time_can_edit)

        user.groups_id |= self.env.ref("stock.group_stock_manager")
        self.assertTrue(self.channel.with_user(user).process_end_time_can_edit)
