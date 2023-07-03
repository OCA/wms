# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    is_shopfloor_created = fields.Boolean()
