# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import models, fields


class StockLocationStorageType(models.Model):

    _name = 'stock.location.storage.type'
    _description = 'Stock location storage type'

    name = fields.Char(required=True)
    location_ids = fields.Many2many(
        'stock.location',
        'stock_location_stock_location_storage_type_rel',
        'stock_location_storage_type_id',
        'stock_location_id',
    )
    allowed_location_ids = fields.Many2many(
        'stock.location',
        'stock_location_allowed_stock_location_storage_type_rel',
        'stock_location_storage_type_id',
        'stock_location_id',
        readonly=True,
    )
    stock_package_storage_type_ids = fields.Many2many(
        'stock.package.storage.type',
        'stock_location_package_storage_type_rel',
        'stock_location_storage_type_id',
        'stock_package_storage_type_id',
    )
