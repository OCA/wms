# Copyright 2025 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields

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

        # Create holiday on scheduled date
        this_year = cls.scheduled_date.year
        holiday_year = cls.env["hr.holidays.public"].create({"year": this_year})
        cls.env["hr.holidays.public.line"].create(
            {
                "name": "holiday 1",
                "date": cls.scheduled_date,
                "year_id": holiday_year.id,
            }
        )
        cls.delivery_date_channel.exclude_public_holidays = True

        # Create specific date channel for partner
        cls._create_channel_partner_date(
            cls.delivery_date_channel,
            cls.partner,
            cls.scheduled_date,
        )

    def test_release_channel_on_specific_date_available(self):
        """Test when channel is open.

        Test that when the specific channel is available, it is assigned even
        if it is a public holiday.
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
