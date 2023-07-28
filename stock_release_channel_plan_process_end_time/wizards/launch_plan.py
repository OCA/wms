# Copyright 2023 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime

from odoo import api, fields, models

from odoo.addons.partner_tz.tools.tz_utils import tz_to_utc_naive_datetime
from odoo.addons.stock_release_channel_process_end_time.utils import float_to_time


class StockReleaseChannelPlanWizardLaunch(models.TransientModel):
    _inherit = "stock.release.channel.plan.wizard.launch"

    process_end_date = fields.Date(
        required=True,
        default=fields.Date.context_today,
    )

    @api.model
    def _action_launch(self, channels):
        channels_to_wakeup = channels.filtered("is_action_wake_up_allowed")
        # Wake up the channels
        super()._action_launch(channels)
        # Override the process end date
        for channel in channels_to_wakeup:
            end_time = float_to_time(channel.process_end_time)  # in TZ
            end_date = datetime.combine(self.process_end_date, end_time)  # in TZ
            tz = channel.process_end_time_tz or "UTC"
            end_date_utc = tz_to_utc_naive_datetime(tz, end_date)
            channel.write({"process_end_date": end_date_utc})
        return
