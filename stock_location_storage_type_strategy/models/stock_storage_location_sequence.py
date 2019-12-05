# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import _, fields, models


class StockStorageLocationSequence(models.Model):

    _name = 'stock.storage.location.sequence'
    _description = 'Storage locations sequence'
    _order = 'sequence'

    package_storage_type_id = fields.Many2one('stock.package.storage.type', required=True)
    sequence = fields.Integer(required=True)
    location_id = fields.Many2one('stock.location', required=True, domain="[('pack_storage_strategy', '!=', 'none')]")

    def _format_package_storage_type_message(self):
        self.ensure_one()
        type_matching_locations = self.location_id.get_storage_locations().filtered(
            lambda l: self.id in l.allowed_location_storage_type_ids.ids
        )
        if type_matching_locations:
            msg = "%s (%s)" % (self.location_id.name, self.location_id.pack_storage_strategy)
        else:
            msg = _("%s (WARNING: no suitable location matching storage type)") % self.location_id.name
        return msg
