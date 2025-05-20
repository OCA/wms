# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class StockReleaseChannelPreparationPlan(models.Model):
    _inherit = "stock.release.channel.preparation.plan"

    depot_id = fields.Many2one("stock.depot")
