# Copyright 2023 Trobz
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    stock_release_use_channel_end_date = fields.Boolean(
        help="Will update scheduled date of picking based on process end date "
        "instead of release date + delay.",
        config_parameter="stock_release_channel_process_end_time."
        "stock_release_use_channel_end_date",
    )
