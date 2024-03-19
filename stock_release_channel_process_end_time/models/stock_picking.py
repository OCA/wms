# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class StockPicking(models.Model):

    _inherit = "stock.picking"

    schedule_date_prior_to_channel_process_end_date_search = fields.Boolean(
        store=False,
        search="_search_schedule_date_prior_to_channel_process_end_date",
        help="Technical field to search on not processed pickings where the scheduled "
        "date is prior to the process end date of available channels.",
    )

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        """Hide schedule_date_prior_to_channel_process_end_date_search from
        filterable/searchable fields"""
        res = super().fields_get(allfields, attributes)
        if res.get("schedule_date_prior_to_channel_process_end_date_search"):
            res["schedule_date_prior_to_channel_process_end_date_search"][
                "searchable"
            ] = False
        return res

    @api.model
    def _search_schedule_date_prior_to_channel_process_end_date(self, operator, value):
        """Search on not processed pickings where the scheduled date is prior to
        the process end date of available channels.

        As we compare dates, we convert datetimes in the timezone of the warehouse
        """
        # We use a searchable field to be able to use 'inselect' operator in
        # order to avoid a subquery in the search method. This is a workaround
        # since the 'inselect' operator is not supported when calling search
        # method but only into search method definition.
        if operator not in ["=", "!="] or not isinstance(value, bool):
            raise UserError(_("Operation not supported"))
        self.env["stock.picking"].flush_model(
            ["release_channel_id", "scheduled_date", "state"]
        )
        self.env["stock.release.channel"].flush_model(
            ["process_end_date", "warehouse_id"]
        )
        query = """
        SELECT
            stock_picking.id
        FROM
            stock_picking
        JOIN stock_release_channel
            ON stock_picking.release_channel_id = stock_release_channel.id
        LEFT JOIN stock_warehouse
            ON stock_warehouse.id = stock_release_channel.warehouse_id
        LEFT JOIN res_partner
            ON stock_warehouse.partner_id = res_partner.id
        , LATERAL (select COALESCE(res_partner.tz, 'UTC') as tz) wh
        WHERE
            stock_picking.state NOT IN ('done', 'cancel')
            AND
              CASE WHEN stock_release_channel.process_end_date is not null
              THEN date(stock_picking.scheduled_date at time zone 'UTC' at time zone wh.tz)
                < date(stock_release_channel.process_end_date
                       at time zone 'UTC' at time zone wh.tz) + interval '1 day'
              ELSE date(stock_picking.scheduled_date at time zone 'UTC' at time zone wh.tz)
                < date(now() at time zone wh.tz) + interval '1 day'
              END
        """
        if value:
            operator_inselect = "inselect" if operator == "=" else "not inselect"
        else:
            operator_inselect = "not inselect" if operator == "=" else "inselect"
        return [("id", operator_inselect, (query, []))]
