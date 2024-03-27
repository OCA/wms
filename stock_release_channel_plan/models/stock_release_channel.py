# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockReleaseChannel(models.Model):
    _inherit = "stock.release.channel"

    preparation_plan_ids = fields.Many2many(
        comodel_name="stock.release.channel.preparation.plan",
        relation="stock_release_channel_preparation_plan_rel",
        column1="channel_id",
        column2="plan_id",
        string="Preparation Plans",
    )
    preparation_weekday_ids = fields.Many2many(
        "time.weekday",
        "release_channel_preparation_weekday_rel",
        "channel_id",
        "weekday_id",
    )
