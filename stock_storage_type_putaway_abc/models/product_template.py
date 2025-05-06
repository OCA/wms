# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import fields, models

from .stock_location import ABC_SELECTION


class ProductTemplate(models.Model):
    _inherit = "product.template"

    abc_storage = fields.Selection(ABC_SELECTION, default="b")
