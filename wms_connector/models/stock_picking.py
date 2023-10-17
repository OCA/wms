# Copyright 2023 Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class StockPicking(models.Model):
    _inherit = ["stock.picking", "synchronize.exportable.mixin"]
    _name = "stock.picking"
