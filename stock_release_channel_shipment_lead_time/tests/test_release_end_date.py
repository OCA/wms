# Copyright 2024 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from freezegun import freeze_time

from odoo import fields

from odoo.addons.stock_release_channel.tests.common import ChannelReleaseCase


class ReleaseChannelEndDateCase(ChannelReleaseCase):
    @freeze_time("2023-01-27 10:00:00")
    def test_channel_counter_release_ready(self):
        self.env["ir.config_parameter"].sudo().set_param(
            "stock_release_channel_process_end_time.stock_release_use_channel_end_date",
            True,
        )
        # Remove existing jobs as some already exists to assign pickings to channel
        jobs_before = self.env["queue.job"].search([])
        jobs_before.unlink()
        # Set the end time
        self.channel.process_end_time = 23.0
        # Set picking scheduled date
        pickings = self.picking | self.picking2 | self.picking3
        pickings.write({"scheduled_date": fields.Datetime.now()})

        # Asleep the release channel to void the process end date
        self.channel.action_sleep()
        self.channel.invalidate_recordset()
        # Execute the picking channel assignations
        self.channel.with_context(test_queue_job_no_delay=True).action_wake_up()

        self.assertEqual(pickings, self.channel.picking_ids)
        # at this stage, the pickings are not ready to be released as the
        # qty available is not enough
        self.assertFalse(self.channel._get_pickings_to_release())

        self._update_qty_in_location(self.loc_bin1, self.product1, 100.0)
        self._update_qty_in_location(self.loc_bin1, self.product2, 100.0)

        self.assertEqual(pickings, self.channel._get_pickings_to_release())
        # if the scheduled date of one picking is changed to be on a time after the
        # process end date but on the same day, it should still be releasable
        pickings[0].scheduled_date = fields.Datetime.from_string("2023-01-27 23:30:00")
        self.assertEqual(pickings, self.channel._get_pickings_to_release())
        # if the scheduled date of one picking is changed to be on a date after the
        # process end date, it should not be releasable anymore
        pickings[0].scheduled_date = fields.Datetime.from_string("2023-01-28 00:00:00")
        self.assertEqual(pickings[1:], self.channel._get_pickings_to_release())

        # Now set channel lead time. It back releasable
        self.channel.shipment_lead_time = 1
        self.assertEqual(pickings, self.channel._get_pickings_to_release())
        # Set date after lead time, it is excluded
        pickings[0].scheduled_date = fields.Datetime.from_string("2023-01-29 00:00:00")
        self.assertEqual(pickings[1:], self.channel._get_pickings_to_release())
