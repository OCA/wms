# Copyright 2023 Camptocamp
# Copyright 2024 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models

from odoo.addons.stock_release_channel_process_end_time.utils import (
    float_to_time,
    time_to_datetime,
)


class StockReleaseChannel(models.Model):
    _inherit = "stock.release.channel"

    cutoff_time = fields.Float(
        help="Fill in this to warning on kanban view if the current time "
        "becomes the cutoff time."
    )
    # Technical field for warning on kanban view
    cutoff_warning = fields.Boolean(compute="_compute_cutoff_warning")

    @api.depends("cutoff_time", "state", "process_end_date", "process_end_time_tz")
    def _compute_cutoff_warning(self):
        now = fields.Datetime.now()
        for channel in self:
            cutoff_warning = False
            if channel.state == "open" and channel.cutoff_time:
                cutoff = time_to_datetime(
                    float_to_time(
                        channel.cutoff_time,
                    ),
                    now=channel.process_end_date,
                    tz=channel.process_end_time_tz,
                )
                cutoff_warning = cutoff < now
            channel.cutoff_warning = cutoff_warning
