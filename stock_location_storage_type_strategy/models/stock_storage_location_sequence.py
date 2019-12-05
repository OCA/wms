# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import _, fields, models


class StockStorageLocationSequence(models.Model):

    _name = 'stock.storage.location.sequence'
    _description = 'Storage locations sequence'
    _order = 'sequence'

    package_storage_type_id = fields.Many2one(
        'stock.package.storage.type', required=True
    )
    sequence = fields.Integer(required=True)
    location_id = fields.Many2one(
        'stock.location',
        required=True,
        domain="[('pack_storage_strategy', '!=', 'none')]",
    )

    def _format_package_storage_type_message(self):
        self.ensure_one()
        type_matching_locations = self.location_id.get_storage_locations().filtered(
            lambda l: self.package_storage_type_id
                      in l.allowed_location_storage_type_ids.mapped(
                          'package_storage_type_ids'
                      )
        )
        if type_matching_locations:
            # Get the selection description
            pack_storage_strat = None
            pack_storage_strat_selection = self.location_id._fields[
                'pack_storage_strategy']._description_selection(self.env)
            for strat in pack_storage_strat_selection:
                if strat[0] == self.location_id.pack_storage_strategy:
                    pack_storage_strat = strat[1]
                    break

            msg = ' * <span style="color: green;">%s (%s)</span>' % (
                self.location_id.name, pack_storage_strat
            )
        else:
            msg = _(
                ' * <span style="color: red;">%s '
                '(WARNING: no suitable location matching storage type)</span>'
            ) % self.location_id.name
        return msg
