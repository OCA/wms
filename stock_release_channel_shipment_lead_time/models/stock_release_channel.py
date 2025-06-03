# Copyright 2023 Camptocamp
# Copyright 2025 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models


class StockReleaseChannel(models.Model):
    _inherit = "stock.release.channel"

    shipment_lead_time = fields.Integer(help="Shipment Lead Time (days)")
    # Migration note: rename shipment_date to delivery_date
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
    delivery_calendar_id = fields.Many2one(
        comodel_name="resource.calendar",
        compute="_compute_delivery_calendar_id",
        store=True,
        help=(
            "Shipment Working Hours. Defaults tot warehouse calendar "
            "for simplicity but another calendar can be used."
        ),
    )

    @api.depends("warehouse_id.calendar_id")
    def _compute_delivery_calendar_id(self):
        for channel in self:
            channel.delivery_calendar_id = channel.warehouse_id.calendar_id

    def _add_shipment_lead_time(self, dt):
        """Add lead time to given datetime.

        If no calendar: dt + lead time
        else: use calendar.plan_days(days, date_from, compute_leaves=True)
            where days is amount of required open days (= lead time + 1)
        """
        self.ensure_one()
        if not self.shipment_lead_time:
            return dt
        dt_tz = self._localize(dt)
        if not self.delivery_calendar_id:
            shipment_tz = fields.Datetime.add(dt_tz, days=self.shipment_lead_time)
        else:
            days = self.shipment_lead_time + 1
            shipment_tz = self.delivery_calendar_id.plan_days(
                days, dt_tz, compute_leaves=True
            )
        shipment_dt = self._naive(shipment_tz, reset_time=True)
        return shipment_dt

    # Migration note: rename _compute_shipment_date to _compute_delivery_date
    @api.depends(
        "process_end_date",
        "shipment_lead_time",
        "delivery_calendar_id",
    )
    def _compute_shipment_date(self):
        for channel in self:
            shipment_date = False
            if channel.process_end_date:
                shipment_date = channel._add_shipment_lead_time(
                    channel.process_end_date
                )
            channel.shipment_date = shipment_date

    @property
    def _delivery_date_generators(self):
        d = super()._delivery_date_generators
        d["delivery"].append(self._next_delivery_date_shipment_lead_time)
        return d

    def _next_delivery_date_shipment_lead_time(self, delivery_date, partner=None):
        """Get the next valid delivery date respecting transport lead time.

        The delivery date must be postponed at least by the shipment lead time.

        A delivery date generator needs to provide the earliest valid date
        starting from the received date. It can be called multiple times with a
        new date to validate.
        """
        arrival_date = self._add_shipment_lead_time(delivery_date)
        while True:
            delivery_date = yield max(delivery_date, arrival_date)
