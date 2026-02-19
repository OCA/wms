from odoo.addons.component.core import Component
from odoo.addons.shopfloor_base.utils import ensure_model


class DataAction(Component):
    _inherit = "shopfloor.data.action"

    @property
    def _packaging_dimension_detail_parser(self):
        return [
            "id",
            "name",
            "qty",
            "packaging_length:length",
            "width",
            "height",
            "weight",
            "length_uom_name",
            "weight_uom_name",
            "barcode",
        ]

    @ensure_model("product.packaging")
    def packaging_dimensions(self, record, **kw):
        return self._jsonify(record, self._packaging_dimension_detail_parser, **kw)
