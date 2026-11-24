# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

from odoo.addons.stock_storage_type_putaway_abc.models.stock_location import (
    ABC_SELECTION,
)


class AbcClassificationLevel(models.Model):

    _inherit = "abc.classification.level"
    _order = "percentage desc, id desc"

    name = fields.Selection(ABC_SELECTION, required=True)

    def name_get(self):
        field_name = self._fields["name"]
        label_by_value = dict(field_name._description_selection(self.env))
        vals = []
        for record in self:
            vals.append((record.id, label_by_value[record.name]))
        return vals
