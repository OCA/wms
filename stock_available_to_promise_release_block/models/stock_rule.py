# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields, models


class StockRule(models.Model):
    _inherit = "stock.rule"

    autoblock_release_on_backorder = fields.Boolean(
        related="route_id.autoblock_release_on_backorder", store=True
    )
