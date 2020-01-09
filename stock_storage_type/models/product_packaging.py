# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import fields, models


class ProductPackaging(models.Model):

    _inherit = "product.packaging"

    package_storage_type_id = fields.Many2one(
        "stock.package.storage.type",
        help="The package storage type will be set on stock packages using "
        "this product packaging, in order to compute its putaway.",
    )
