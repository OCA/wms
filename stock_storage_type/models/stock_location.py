# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import api, models, fields


class StockLocation(models.Model):

    _inherit = 'stock.location'

    stock_location_storage_type_ids = fields.Many2many(
        'stock.location.storage.type',
        'stock_location_stock_location_storage_type_rel',
        'stock_location_id',
        'stock_location_storage_type_id',
    )

    allowed_stock_location_storage_type_ids = fields.Many2many(
        'stock.location.storage.type',
        'stock_location_allowed_stock_location_storage_type_rel',
        'stock_location_id',
        'stock_location_storage_type_id',
        compute='_compute_allowed_stock_location_storage_type_ids',
        store=True,
    )

    @api.depends(
        'stock_location_storage_type_ids', 'location_id',
        'location_id.allowed_stock_location_storage_type_ids'
    )
    def _compute_allowed_stock_location_storage_type_ids(self):
        for location in self:
            if location.stock_location_storage_type_ids:
                location.allowed_stock_location_storage_type_ids = [
                    (6, 0, location.stock_location_storage_type_ids.ids)
                ]
            else:
                parent = location.location_id
                location.allowed_stock_location_storage_type_ids = [
                    (6, 0,
                     parent.allowed_stock_location_storage_type_ids.ids)
                ]
