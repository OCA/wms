# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from datetime import timedelta

from freezegun import freeze_time

from odoo import fields

from odoo.addons.stock_release_channel.tests.common import ChannelReleaseCase


class ReleaseChannelEndDateCase(ChannelReleaseCase):
    @classmethod
    @freeze_time("2023-09-01")
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.holiday_model = cls.env["hr.holidays.public"]
        cls.holiday_model_line = cls.env["hr.holidays.public.line"]

        # Remove possibly existing public holidays that would interfer.
        cls.holiday_model_line.search([]).unlink()
        cls.holiday_model.search([]).unlink()

        # Create holidays
        holiday_date = fields.Datetime.now() + timedelta(days=17)  # 2023-09-18
        this_year = holiday_date.year
        holiday_1 = cls.holiday_model.create({"year": this_year})
        cls.holiday_model_line.create(
            {"name": "holiday 1", "date": holiday_date, "year_id": holiday_1.id}
        )
        cls.holiday_date = holiday_date
        cls.holiday_1 = holiday_1

    def _assign_picking(self, picking):
        picking.release_channel_id = False
        picking.assign_release_channel()

    @freeze_time("2023-09-01")
    def test_assign_channel(self):
        self.channel.exclude_public_holidays = True
        self.channel.process_end_time = 0
        self.channel.process_end_date = self.holiday_date
        self._assign_picking(self.picking)
        self.assertNotEqual(self.channel, self.picking.release_channel_id)

        # Country
        self.holiday_1.country_id = self.env.ref("base.us")
        self._assign_picking(self.picking)
        self.assertEqual(self.channel, self.picking.release_channel_id)
        self.picking.partner_id.country_id = self.holiday_1.country_id
        self._assign_picking(self.picking)
        self.assertNotEqual(self.channel, self.picking.release_channel_id)

        # State
        self.holiday_1.line_ids[0].state_ids = self.env.ref("base.state_us_35")
        self._assign_picking(self.picking)
        self.assertEqual(self.channel, self.picking.release_channel_id)
        self.picking.partner_id.state_id = self.env.ref("base.state_us_35")
        self._assign_picking(self.picking)
        self.assertNotEqual(self.channel, self.picking.release_channel_id)
