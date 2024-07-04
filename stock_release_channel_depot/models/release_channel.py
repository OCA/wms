# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class StockReleaseChannel(models.Model):
    _inherit = "stock.release.channel"

    depot_id = fields.Many2one("stock.depot")
