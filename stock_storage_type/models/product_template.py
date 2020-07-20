# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import fields, models


class ProductTemplate(models.Model):

    _inherit = "product.template"

    product_package_storage_type_id = fields.Many2one(
        "stock.package.storage.type",
        string="Package storage type",
        help="Defines a 'default' package storage type for this product to be "
        "applied on packages without product packagings for put-away "
        "computations.",
    )
