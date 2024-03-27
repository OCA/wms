# Copyright 2024 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    release_channel_show_last_picking_done = fields.Boolean(
        string="Channels dashboard - Show last delivery done",
        help="In release channels dashboard, add link to last done picking "
        "and show transfer date",
    )
    recompute_channel_on_pickings_at_release = fields.Boolean(
        help="When releasing a transfer, recompute channel",
        default=True,
    )
