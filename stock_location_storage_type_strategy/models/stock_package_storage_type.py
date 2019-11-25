# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import _, fields, models


class StockPackageStorageType(models.Model):

    _inherit = 'stock.package.storage.type'

    package_storage_location_ids = fields.One2many(
        'stock.package.storage.location',
        'package_storage_type_id',
        string='Storage locations',
    )

    def action_view_storage_locations(self):
        return {
            'name': _('Storage locations'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.package.storage.location',
            'view_mode': 'list',
            'domain': [('package_storage_type_id', '=', self.id)],
            'context': {'default_package_storage_type_id': self.id},
        }
