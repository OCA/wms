# Copyright 2024 Camptocamp SA
# Copyright 2024 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields

from .common import ReleaseChannelPartnerDateCommon


class TestReleaseChannelPartnerDate(ReleaseChannelPartnerDateCommon):
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

    def test_release_channel_on_specific_date_not_available(self):
        """Test that when no release channel is available to satisfy
        a specific partner date,no fallback release channel is
        proposed."""
        # Exclude delivery channel from possible candidates
        self.delivery_date_channel.picking_type_ids = self.env[
            "stock.picking.type"
        ].search([("id", "!=", self.move.picking_id.picking_type_id.id)], limit=1)
        scheduled_date = fields.Datetime.now()
        self._create_channel_partner_date(
            self.delivery_date_channel,
            self.partner,
            scheduled_date,
        )
        self.move.picking_id.scheduled_date = scheduled_date
        self.move.picking_id.assign_release_channel()
        self.assertFalse(self.move.picking_id.release_channel_id)
