# Copyright 2024 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    release_channel_show_last_picking_done = fields.Boolean(
        related="company_id.release_channel_show_last_picking_done",
        readonly=False,
    )
    recompute_channel_on_pickings_at_release = fields.Boolean(
        related="company_id.recompute_channel_on_pickings_at_release",
        readonly=False,
    )
