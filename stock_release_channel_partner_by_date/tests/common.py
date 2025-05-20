# Copyright 2024 Camptocamp SA
# Copyright 2024 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)


from odoo.addons.stock_release_channel.tests.test_release_channel_partner import (
    ReleaseChannelPartnerCommon,
)


class ReleaseChannelPartnerDateCommon(ReleaseChannelPartnerCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.delivery_date_channel = cls.partner_channel.copy(
            {
                "name": "Specific Date Channel",
                "warehouse_id": cls.wh.id,
            }
        )

    @classmethod
    def _create_channel_partner_date(cls, channel, partner, date):
        rc_date_model = cls.env["stock.release.channel.partner.date"]
        return rc_date_model.create(
            {
                "partner_id": partner.id,
                "release_channel_id": channel.id,
                "date": date,
            }
        )
