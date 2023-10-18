# Copyright 2023 Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockPicking(models.Model):
    _inherit = ["synchronize.exportable.mixin", "stock.picking"]
    _name = "stock.picking"
