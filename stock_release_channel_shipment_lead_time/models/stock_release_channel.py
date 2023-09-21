# Copyright 2023 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
from datetime import timedelta

from odoo import api, fields, models


class StockReleaseChannel(models.Model):
    _inherit = "stock.release.channel"

    shipment_lead_time = fields.Integer(help="Shipment Lead Time (days)")
    shipment_date = fields.Date(
        compute="_compute_shipment_date",
        store=True,
        help=(
            "if no warehouse or no calendar on the warehouse:"
            "process end date + shipment lead time."
            "Otherwise, it's counted by calendar included leaves:"
            "number of days = lead time + 1"
        ),
    )

    @api.depends(
        "process_end_date",
        "shipment_lead_time",
        "warehouse_id",
        "warehouse_id.calendar_id",
    )
    def _compute_shipment_date(self):
        """
        if no warehouse or no calendar on the warehouse:
            process end date + lead time
        else: use calendar.plan_days(days, date_from, compute_leaves=True)
            where days is amount of required open days (= lead time + 1)
        """
        for channel in self:
            shipment_date = False
            if channel.process_end_date:
                shipment_date = channel.process_end_date + timedelta(
                    days=channel.shipment_lead_time
                )
                if channel.warehouse_id.calendar_id:
                    days = channel.shipment_lead_time + 1
                    shipment_date = channel.warehouse_id.calendar_id.plan_days(
                        days, channel.process_end_date, compute_leaves=True
                    )
            channel.shipment_date = shipment_date
