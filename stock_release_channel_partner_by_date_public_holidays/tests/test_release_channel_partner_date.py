# Copyright 2025 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields

from odoo.addons.stock_release_channel_partner_by_date.tests.common import (
    ReleaseChannelPartnerDateCommon,
)


class TestReleaseChannelPartnerDate(ReleaseChannelPartnerDateCommon):
    def test_release_channel_on_specific_date_not_available(self):
        """Test that when no release channel is available to satisfy
        a specific partner date, no fallback release channel is
        proposed."""
        scheduled_date = fields.Datetime.now()

        # Create holiday
        this_year = scheduled_date.year
        holiday_year = self.env["hr.holidays.public"].create({"year": this_year})
        self.env["hr.holidays.public.line"].create(
            {"name": "holiday 1", "date": scheduled_date, "year_id": holiday_year.id}
        )
        self._create_channel_partner_date(
            self.delivery_date_channel,
            self.partner,
            scheduled_date,
        )
        self.move.picking_id.scheduled_date = scheduled_date
        self.move.picking_id.assign_release_channel()
        self.assertFalse(self.move.picking_id.release_channel_id)
