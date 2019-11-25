# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import fields, models


class StockPackageStorageLocation(models.Model):

    _name = 'stock.package.storage.location'
    _description = 'Storage locations for related package storage type'
    _order = 'sequence'

    package_storage_type_id = fields.Many2one('stock.package.storage.type', required=True)
    sequence = fields.Integer(required=True)
    location_id = fields.Many2one('stock.location', required=True)
