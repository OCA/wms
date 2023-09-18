# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class StockReleaseChannel(models.Model):

    _inherit = "stock.release.channel"

    exclude_public_holidays = fields.Boolean()

    def filter_release_channel(self, partner):
        channels = self
        for channel in self:
            if not channel.exclude_public_holidays:
                continue
            if channel._is_shipment_date_a_public_holiday(partner):
                channels -= channel
        return channels

    def _is_shipment_date_a_public_holiday(self, partner):
        """
        Returns True if shipment_date is a public holiday
        :return: bool
        """
        self.ensure_one()
        res = False
        shipment_date = self.shipment_date
        if not shipment_date:
            return res
        domain = [
            ("year_id.country_id", "in", (False, partner.country_id.id)),
            "|",
            ("state_ids", "=", False),
            ("state_ids", "=", partner.state_id.id),
            ("date", "=", shipment_date),
        ]
        hhplo = self.env["hr.holidays.public.line"]
        holidays_line = hhplo.search(domain, limit=1, order="id")
        return bool(holidays_line)
