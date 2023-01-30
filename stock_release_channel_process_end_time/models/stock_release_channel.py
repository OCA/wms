# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

from ..utils import float_to_time, next_datetime


class StockReleaseChannel(models.Model):

    _inherit = "stock.release.channel"

    process_end_time = fields.Float(
        help="Fill in this to indicates when this channel release process would"
        "be ended. This information will be used to compute the channel pickings"
        "scheduled date at channel awaking.",
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
                channel.process_end_date = next_datetime(
                    now, float_to_time(channel.process_end_time)
                )
            elif channel.state == "asleep":
                channel.process_end_date = False

    @api.model
    def assign_release_channel(self, picking):
        res = super().assign_release_channel(picking)
        # Check if a channel has been assigned to the picking and write scheduled_date
        # if different to avoid unnecessary write
        if (
            picking.release_channel_id
            and picking.scheduled_date != picking.release_channel_id.process_end_date
        ):
            picking.scheduled_date = picking.release_channel_id.process_end_date
        return res
