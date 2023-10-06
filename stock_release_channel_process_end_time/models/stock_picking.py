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
        """
        # We use a searchable field to be able to use 'inselect' operator in
        # order to avoid a subquery in the search method. This is a workaround
        # since the 'inselect' operator is not supported when calling search
        # method but only into search method definition.
        if operator not in ["=", "!="] or not isinstance(value, bool):
            raise UserError(_("Operation not supported"))
        query = """
        SELECT
            stock_picking.id
        FROM
            stock_picking
        WHERE
            stock_picking.state NOT IN ('done', 'cancel')
            AND exists (
                SELECT
                    TRUE
                FROM
                    stock_release_channel
                WHERE
                    stock_release_channel.process_end_date is not null
                    and stock_picking.scheduled_date <= stock_release_channel.process_end_date
            )
        """
        if value:
            operator_inselect = "inselect" if operator == "=" else "not inselect"
        else:
            operator_inselect = "not inselect" if operator == "=" else "inselect"
        return [("id", operator_inselect, (query, []))]

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
                rec.release_channel_id
                and rec.release_channel_id.process_end_date
                and rec.scheduled_date != rec.release_channel_id.process_end_date
                and enabled_update_scheduled_date
            ):
                rec.scheduled_date = rec.release_channel_id.process_end_date
        return res
