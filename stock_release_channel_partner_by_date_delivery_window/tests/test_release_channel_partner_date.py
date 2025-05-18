# Copyright 2025 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields
from odoo.fields import Command

from odoo.addons.stock_release_channel_partner_by_date.tests.common import (
    ReleaseChannelPartnerDateCommon,
)


class TestReleaseChannelPartnerDate(ReleaseChannelPartnerDateCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.scheduled_date = fields.Datetime.now()
        cls.move.picking_id.scheduled_date = cls.scheduled_date
        cls.move.picking_id.date_deadline = cls.scheduled_date

        # Create partner delivery window on a date different from scheduled
        weekday = (cls.scheduled_date.weekday() + 3) % 6
        time_weekday = cls.env["time.weekday"].search([("name", "=", str(weekday))])
        cls.partner.write(
            {
                "delivery_time_preference": "time_windows",
                "delivery_time_window_ids": [
                    Command.create(
                        {
                            "time_window_start": 8.00,
                            "time_window_end": 18.50,
                            "time_window_weekday_ids": [Command.link(time_weekday.id)],
                        }
                    )
                ],
            }
        )

        # Create specific date channel for partner
        cls._create_channel_partner_date(
            cls.delivery_date_channel,
            cls.partner,
            cls.scheduled_date,
        )

    def test_release_channel_on_specific_date_available(self):
        """Test when channel is open.

        Test that when the specific channel is available, it is assigned even
        if it is not in the delivery window.
        """
        self.delivery_date_channel.action_wake_up()
        self.delivery_date_channel.shipment_date = self.scheduled_date
        self.move.picking_id.assign_release_channel()
        self.assertEqual(
            self.move.picking_id.release_channel_id, self.delivery_date_channel
        )

    def test_release_channel_on_specific_date_not_available(self):
        """Test when channel is asleep.

        Test that when no release channel is available to satisfy
        a specific partner date, no fallback release channel is
        proposed.
        """
        self.move.picking_id.assign_release_channel()
        self.assertFalse(self.move.picking_id.release_channel_id)
