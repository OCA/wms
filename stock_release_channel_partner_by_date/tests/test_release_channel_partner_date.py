# Copyright 2024 Camptocamp SA
# Copyright 2024 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields

from odoo.addons.stock_release_channel.tests.test_release_channel_partner import (
    ReleaseChannelPartnerCommon,
)


class TestReleaseChannelPartnerDate(ReleaseChannelPartnerCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.delivery_date_channel = cls.partner_channel.copy(
            {"name": "Specific Date Channel"}
        )

    def _create_channel_partner_date(self, channel, partner, date):
        rc_date_model = self.env["stock.release.channel.partner.date"]
        return rc_date_model.create(
            {
                "partner_id": partner.id,
                "release_channel_id": channel.id,
                "date": date,
            }
        )

    def test_release_channel_on_specific_date(self):
        """partner specific date release channel is higher priority than other channels"""
        self.delivery_date_channel.action_wake_up()
        scheduled_date = fields.Datetime.now()
        self.move.picking_id.scheduled_date = scheduled_date
        self._create_channel_partner_date(
            self.delivery_date_channel,
            self.partner,
            scheduled_date,
        )
        self.moves.picking_id.assign_release_channel()
        self.assertEqual(
            self.move.picking_id.release_channel_id, self.delivery_date_channel
        )
        self.assertEqual(self.move2.picking_id.release_channel_id, self.other_channel)

    def test_release_channel_sleep_archive_specific_date(self):
        self.delivery_date_channel.action_wake_up()
        channel_date = self._create_channel_partner_date(
            self.delivery_date_channel,
            self.partner,
            fields.Date.today(),
        )
        self.assertTrue(channel_date.active)
        self.delivery_date_channel.action_sleep()
        self.assertFalse(channel_date.active)
