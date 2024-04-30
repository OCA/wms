# Copyright 2023 Trobz
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    stock_sale_report_display_is_available = fields.Boolean(
        related="company_id.stock_sale_report_display_is_available",
        readonly=False,
    )
