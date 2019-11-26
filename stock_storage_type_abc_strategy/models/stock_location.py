# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import api, models, fields


ABC_SELECTION = [('a', 'A'), ('b', 'B'), ('c', 'C')]


class StockLocation(models.Model):

    _inherit = 'stock.location'

    pack_storage_strategy = fields.Selection(
        selection_add=[('abc', 'Chaotic ABC')]
    )
    display_abc_storage = fields.Boolean(
        compute='_compute_display_abc_storage'
    )
    abc_storage = fields.Selection(ABC_SELECTION, required=True, default='b')

    @api.depends(
        'location_id', 'location_id.pack_storage_strategy',
        'location_id.display_abc_storage'
    )
    def _compute_display_abc_storage(self):
        for location in self:
            current_location = location.location_id
            display_abc_storage = current_location.display_abc_storage
            while current_location and not display_abc_storage:
                if current_location.pack_storage_strategy == 'abc':
                    display_abc_storage = True
                    break
                else:
                    current_location = current_location.location_id
            location.display_abc_storage = display_abc_storage

    def get_storage_locations(self, product=None):
        if not self.pack_storage_strategy == 'abc':
            return super().get_storage_locations()
        return self._get_abc_locations(product)

    def _get_abc_locations(self, product):
        locations = self.search(
            [('id', 'child_of', self.ids), ('id', '!=', self.id)],
            order='abc_storage ASC'
        )
        return locations._sort_abc_locations(product.abc_storage)

    def _sort_abc_locations(self, product_abc):
        locations = self
        if product_abc == 'a':
            # Already ordered, no need to reorder
            pass
        else:
            a_locations = b_locations = c_locations = self.browse()
            for loc in self:
                if loc.abc_storage == 'a':
                    a_locations |= loc
                elif loc.abc_storage == 'b':
                    b_locations |= loc
                elif loc.abc_storage == 'c':
                    c_locations |= loc
            if product_abc == 'b':
                locations = b_locations | c_locations | a_locations
            elif product_abc == 'c':
                locations = c_locations | a_locations | b_locations
        return locations
