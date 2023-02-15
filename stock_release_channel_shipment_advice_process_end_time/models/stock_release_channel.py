# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import api, fields, models


class StockReleaseChannel(models.Model):

    _inherit = "stock.release.channel"
    shipment_advice_arrival_delay = fields.Integer(
        compute="_compute_shipment_advice_arrival_delay",
        store=True,
        readonly=False,
        help="The delay between the release channel process end time and the arrival "
        "of shipments to the dock.",
    )
    shipment_advice_arrival_time = fields.Float(
        "Arrival to dock at",
        compute="_compute_shipment_advice_arrival_time",
        inverse="_inverse_shipment_advice_arrival_time",
    )
    shipment_advice_departure_delay = fields.Integer(
        compute="_compute_shipment_advice_departure_delay",
        store=True,
        readonly=False,
        help="The delay between the release channel process end time and the departure "
        "of shipments to the dock.",
    )
    shipment_advice_departure_time = fields.Float(
        "Departure from dock at",
        compute="_compute_shipment_advice_departure_time",
        inverse="_inverse_shipment_advice_departure_time",
    )

    @api.depends("process_end_time", "shipment_advice_departure_delay")
    def _compute_shipment_advice_departure_time(self):
        for rec in self:
            rec.shipment_advice_departure_time = rec.process_end_time + (
                rec.shipment_advice_departure_delay / 60
            )

    def _inverse_shipment_advice_departure_time(self):
        for rec in self:
            rec.shipment_advice_departure_delay = (
                rec.shipment_advice_departure_time - rec.process_end_time
            ) * 60

    @api.depends("process_end_time", "shipment_advice_arrival_delay")
    def _compute_shipment_advice_arrival_time(self):
        for rec in self:
            rec.shipment_advice_arrival_time = rec.process_end_time + (
                rec.shipment_advice_arrival_delay / 60
            )

    def _inverse_shipment_advice_arrival_time(self):
        for rec in self:
            rec.shipment_advice_arrival_delay = (
                rec.shipment_advice_arrival_time - rec.process_end_time
            ) * 60

    @api.depends("warehouse_id")
    def _compute_shipment_advice_arrival_delay(self):
        for rec in self:
            if not rec.shipment_advice_arrival_delay:
                rec.shipment_advice_arrival_delay = (
                    rec.warehouse_id.release_channel_shipment_advice_arrival_delay
                )

    @api.depends("warehouse_id")
    def _compute_shipment_advice_departure_delay(self):
        for rec in self:
            if not rec.shipment_advice_departure_delay:
                rec.shipment_advice_departure_delay = (
                    rec.warehouse_id.release_channel_shipment_advice_departure_delay
                )

    def _get_shipment_advice_arrival_date(self):
        self.ensure_one()
        return (
            self.process_end_date
            + timedelta(minutes=self.shipment_advice_arrival_delay)
            if self.process_end_date
            else self.process_end_date
        )

    def _get_shipment_advice_departure_date(self):
        self.ensure_one()
        return (
            self.process_end_date
            + timedelta(minutes=self.shipment_advice_departure_delay)
            if self.process_end_date
            else self.process_end_date
        )
