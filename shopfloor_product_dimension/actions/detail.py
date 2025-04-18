# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.addons.component.core import Component


class DataDetailAction(Component):
    _inherit = "shopfloor.data.detail.action"

    @property
    def _product_dimension_parser(self):
        return [
            "product_length:length",
            "product_height:height",
            "product_width:width",
            "weight",
            (
                "dimensional_uom_id:dimension_uom",
                self._simple_record_parser() + ["factor", "rounding"],
            ),
            (
                "weight_uom_id:weight_uom",
                self._simple_record_parser() + ["factor", "rounding"],
            ),
        ]

    def product_detail(self, record, **kw):
        data = super().product_detail(record, **kw)
        dimensions_data = self._jsonify(record, self._product_dimension_parser)
        data.update(dimensions_data)
        return data
