# Copyright 2025 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


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

    delivery_date_weekday = fields.Integer(
        compute="_compute_delivery_date_weekday",
        store=True,
    )

    # Migration note: shipment_date will be renamed to delivery_date
    @api.depends(
        "shipment_date",
    )
    def _compute_delivery_date_weekday(self):
        for channel in self:
            if channel.shipment_date:
                channel.delivery_date_weekday = channel.shipment_date.weekday()
            else:
                channel.delivery_date_weekday = -1
