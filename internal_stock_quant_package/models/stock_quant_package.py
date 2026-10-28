# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockQuantPackage(models.Model):

    _inherit = "stock.quant.package"

    is_internal = fields.Boolean("Internal use?")
