# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import fields, models


class ProductTemplate(models.Model):

    _inherit = "product.template"

    package_type_id = fields.Many2one(
        "stock.package.type",
        string="Package type",
        help="Defines a 'default' package type for this product to be "
        "applied on packages without product packagings and on put-away "
        "computation based on package type for product not in a package",
    )
