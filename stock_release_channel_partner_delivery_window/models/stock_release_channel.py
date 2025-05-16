# Copyright 2025 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class StockReleaseChannel(models.Model):

    _inherit = "stock.release.channel"

    respect_partner_delivery_time_windows = fields.Boolean(
        string="Respect Partner Delivery time windows",
        default=False,
        help=(
            "If the delivery has moves linked to SO lines linked to SO that has"
            " a commitment_date, then we never respect the partner time window "
            "(it is not an exclusion selection criteria anymore)"
        ),
    )

    def filter_release_channel_partner_window(self, picking, partner):
        if picking.sale_id.commitment_date:
            # Date is forced on SO, don't filter
            return self
        return self.filtered(
            lambda channel: not channel.respect_partner_delivery_time_windows
            or (
                channel.shipment_date
                and channel.shipment_date.weekday() in partner.delivery_time_weekdays
            )
        )
