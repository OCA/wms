# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

from odoo import api, fields, models


class StockReleaseChannel(models.Model):
    _inherit = "stock.release.channel"

    delivery_weekday_ids = fields.Many2many(
        "time.weekday",
        "release_channel_delivery_weekday_rel",
        "channel_id",
        "weekday_id",
        string="Delivery weekdays",
    )
    preparation_weekday_ids = fields.Many2many(
        "time.weekday",
        compute="_compute_preparation_weekday_ids",
        readonly=True,
        store=True,
    )

    @api.depends("delivery_weekday_ids", "shipment_lead_time")
    def _compute_preparation_weekday_ids(self):
        """Preparation weekdays are delivery weekdays - lead time"""
        for channel in self:
            weekday_names = []
            delivery_weekdays = channel.delivery_weekday_ids
            for wd in delivery_weekdays:
                if channel.warehouse_id.calendar_id:
                    # To consider days off in the calendar, we look for the next date
                    #  from today on whose weekday matches with current delivery weekday.
                    # We then deduce the lead time using the calendar to find a weekday
                    #  that is open.
                    # As this serves for helping in configuring the static preparation
                    #  plan, we do not consider here the leaves.
                    date_from = wd._get_next_weekday_date()
                    date_from_minus_lead = channel.warehouse_id.calendar_id.plan_days(
                        -channel.shipment_lead_time,
                        fields.Datetime.to_datetime(date_from),
                    )
                    weekday_names.append(str(date_from_minus_lead.weekday()))
                else:
                    # If we don't have a calendar, deduce lead time and look
                    #  for corresponding weekday
                    wd_minus_lead = int(wd.name) - channel.shipment_lead_time
                    if wd_minus_lead < 0:
                        while not 0 <= wd_minus_lead < 7:
                            wd_minus_lead += 7
                    weekday_names.append(str(wd_minus_lead))
            channel.preparation_weekday_ids = self.env["time.weekday"].search(
                [("name", "in", weekday_names)]
            )
