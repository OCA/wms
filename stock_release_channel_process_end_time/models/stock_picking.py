# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class StockPicking(models.Model):

    _inherit = "stock.picking"

    # TODO: move this field to stock_release_channel so that we don't have to alter
    # _field_picking_domains.
    scheduled_date_prior_to_channel_end_date_search = fields.Boolean(
        store=False,
        search="_search_scheduled_date_prior_to_channel_end_date",
        help="Technical field to search on not processed pickings where the scheduled "
        "date is prior to the end date of related channel.",
    )

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        # Hide scheduled_date_prior_to_channel_end_date_search from
        # filterable/searchable fields
        res = super().fields_get(allfields, attributes)
        if res.get("scheduled_date_prior_to_channel_end_date_search"):
            res["scheduled_date_prior_to_channel_end_date_search"]["searchable"] = False
        return res

    @api.model
    def _search_scheduled_date_prior_to_channel_end_date_condition(self):
        self.env["stock.release.channel"].flush_model(["process_end_date"])
        self.env["stock.picking"].flush_model(["scheduled_date"])
        end_date = (
            "date(stock_release_channel.process_end_date "
            "at time zone 'UTC' at time zone wh.tz) "
        )
        now = fields.Datetime.now()
        cond = f"""
            CASE WHEN stock_release_channel.process_end_date is not null
            THEN date(stock_picking.scheduled_date at time zone 'UTC' at time zone wh.tz)
            < {end_date} + interval '1 day'
            ELSE date(stock_picking.scheduled_date at time zone 'UTC' at time zone wh.tz)
            < date(TIMESTAMP %s at time zone wh.tz) + interval '1 day'
            END
        """
        return cond, [now]

    @api.model
    def _search_scheduled_date_prior_to_channel_end_date(self, operator, value):
        """Search on not processed pickings where the scheduled date is prior to
        the end date of related channel.

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
        """
        (
            cond_q,
            params,
        ) = self._search_scheduled_date_prior_to_channel_end_date_condition()
        query += cond_q

        if value:
            operator_inselect = "inselect" if operator == "=" else "not inselect"
        else:
            operator_inselect = "not inselect" if operator == "=" else "inselect"
        return [("id", operator_inselect, (query, params))]

    def _after_release_set_expected_date(self):
        enabled_update_scheduled_date = bool(
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(
                "stock_release_channel_process_end_time.stock_release_use_channel_end_date"
            )
        )
        res = super()._after_release_set_expected_date()
        for rec in self:
            # Check if a channel has been assigned to the picking and write
            # scheduled_date if different to avoid unnecessary write
            if (
                rec.state not in ("done", "cancel")
                and rec.release_channel_id
                and rec.release_channel_id.process_end_date
                and rec.scheduled_date != rec.release_channel_id.process_end_date
                and enabled_update_scheduled_date
            ):
                rec.scheduled_date = rec.release_channel_id.process_end_date
        return res
