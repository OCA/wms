# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import models, fields


class ProductPackaging(models.Model):

    _inherit = 'product.packaging'

    stock_package_storage_type_id = fields.Many2one(
        'stock.package.storage.type'
    )
