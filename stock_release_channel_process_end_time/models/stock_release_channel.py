# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models

from odoo.addons.base.models.res_partner import _tz_get

from ..utils import float_to_time, next_datetime


class StockReleaseChannel(models.Model):

    _inherit = "stock.release.channel"

    process_end_time = fields.Float(
        help="Fill in this to indicates when this channel release process would "
        "be ended. This information will be used to compute the channel pickings "
        "scheduled date at channel awaking.",
    )
    process_end_time_tz = fields.Selection(
        selection=_tz_get,
        compute="_compute_process_end_time_tz",
        help="Technical field to compute the timezone for the process end time.",
    )
    process_end_time_can_edit = fields.Boolean(
        compute="_compute_process_end_time_can_edit",
        help="Technical field in order to know if user can edit the end date in views",
    )
    process_end_date = fields.Datetime(
        compute="_compute_process_end_date",
        store=True,
        readonly=False,
        help="This is the end date for this window of opened channel.",
    )

    @api.depends_context("uid")
    def _compute_process_end_time_can_edit(self):
        if self.user_has_groups("stock.group_stock_manager"):
            self.update({"process_end_time_can_edit": True})
        else:
            self.update({"process_end_time_can_edit": False})

    @api.depends("state", "process_end_time")
    def _compute_process_end_date(self):
        now = fields.Datetime.now()
        for channel in self:
            # We check if a date is not already set (manually)
            if channel.state != "asleep" and not channel.process_end_date:
                end = next_datetime(
                    now,
                    float_to_time(
                        channel.process_end_time,
                        tz=channel.process_end_time_tz,
                    ),
                )
                channel.process_end_date = end
            elif channel.state == "asleep":
                channel.process_end_date = False

    @api.depends("warehouse_id.partner_id.tz")
    @api.depends_context("company")
    def _compute_process_end_time_tz(self):
        # As the time is timezone-agnostic, we use the channel warehouse adress timezone
        # or the company one, either it will be considered as UTC
        company_tz = self.env.company.partner_id.tz
        for channel in self:
            channel.process_end_time_tz = (
                channel.warehouse_id.partner_id.tz or company_tz or "UTC"
            )

    @api.model
    def assign_release_channel(self, picking):
        res = super().assign_release_channel(picking)
        picking._after_release_set_expected_date()
        return res

    def _field_picking_domains(self):
        res = super()._field_picking_domains()
        release_ready_domain = res["count_picking_release_ready"]
        # the initial scheduled_date condition based on datetime.now() must
        # be replaced by a condition based on the process_end_date
        # since the processe_end_date is a field on the release channel
        # and not on the picking we all use an 'inselect' operator
        # (join in where clause is not possible). The 'inselect' operator
        # is not available in the ORM so we use a search with a domain
        # on a specialized field defined in the stock.picking model
        # (see stock.picking._search_schedule_date_prior_to_channel_process_end_date)
        new_domain = []
        for criteria in release_ready_domain:
            if criteria[0] == "scheduled_date":
                new_domain.append(
                    (
                        "schedule_date_prior_to_channel_process_end_date_search",
                        "=",
                        True,
                    )
                )
            else:
                new_domain.append(criteria)
        res["count_picking_release_ready"] = new_domain
        return res
