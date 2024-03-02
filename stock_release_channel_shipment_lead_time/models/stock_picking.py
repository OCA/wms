# Copyright 2023 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# Copyright 2023 Camptocamp
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _get_release_channel_possible_candidate_domain(self):
        # Exclude deliveries (OUT pickings) when the date_deadline is after the shipment date
        domain = super()._get_release_channel_possible_candidate_domain()

        date = self.date_deadline
        if date:
            # date is datetime UTC => convert to local time to compare
            # with shipment_date which is local date
            tz = (
                self.picking_type_id.warehouse_id.partner_id.tz
                or self.company_id.partner_id.tz
            )
            date = fields.Datetime.context_timestamp(
                self.with_context(tz=tz), date
            ).date()

            domain.extend(
                [
                    "|",
                    ("shipment_date", "=", False),
                    ("shipment_date", ">=", date),
                ]
            )
        return domain

    @api.model
    def _search_scheduled_date_prior_to_channel_end_date_condition(self):
        self.env["stock.release.channel"].flush_model(
            ["process_end_date", "shipment_date", "shipment_lead_time"]
        )
        self.env["stock.picking"].flush_model(["scheduled_date"])
        end_date = "stock_release_channel.shipment_date"
        # We don't consider warehouse calendar when there is no process end date
        lead_time = (
            "interval '1 day' * coalesce(stock_release_channel.shipment_lead_time, 0)"
        )
        now = fields.Datetime.now()
        cond = f"""
            CASE WHEN stock_release_channel.process_end_date is not null
            THEN date(stock_picking.scheduled_date at time zone 'UTC' at time zone wh.tz)
            < {end_date} + interval '1 day'
            ELSE date(stock_picking.scheduled_date at time zone 'UTC' at time zone wh.tz)
            < date(TIMESTAMP %s at time zone wh.tz) + {lead_time} + interval '1 day'
            END
        """
        return cond, [now]
