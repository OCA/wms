# Copyright 2023 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)


from odoo import api, fields, models

from odoo.addons.stock_release_channel_process_end_time.utils import float_to_time


class StockReleaseChannel(models.Model):
    _inherit = "stock.release.channel"

    cutoff_time = fields.Float(
        help="Fill in this to warning on kanban view if the current time "
        "becomes the cutoff time."
    )
    # Technical field for warning on kanban view
    cutoff_warning = fields.Boolean(compute="_compute_cutoff_warning")

    @api.depends_context("tz")
    @api.depends("cutoff_time", "state")
    def _compute_cutoff_warning(self):
        now = fields.Datetime.now()
        for rec in self:
            if rec.cutoff_time and rec.process_end_date:
                hours = float_to_time(
                    rec.cutoff_time,
                    tz=rec.env.user.tz or "UTC",
                )
                datetime = rec.process_end_date.replace(
                    hour=hours.hour, minute=hours.minute, second=0, microsecond=0
                )
                if hours.tzinfo:
                    datetime += hours.utcoffset()
                rec.cutoff_warning = (
                    True if datetime < now and rec.state == "open" else False
                )
            else:
                rec.cutoff_warning = False
