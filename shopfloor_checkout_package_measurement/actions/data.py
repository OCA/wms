# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
from odoo.addons.component.core import Component
from odoo.addons.shopfloor_base.utils import ensure_model


class DataAction(Component):
    _inherit = "shopfloor.data.action"

    @property
    def _package_parser(self):
        res = super()._package_parser
        res.extend(
            [
                "pack_length:length",
                "width",
                "height",
                "shipping_weight",
                ("length_uom_id:dimension_uom", self._simple_record_parser()),
                ("weight_uom_id:weight_uom", self._simple_record_parser()),
            ]
        )
        return res

    @ensure_model("product.packaging")
    def package_requirement(self, record, **kw):
        return self._jsonify(record, self._package_requirement_parser, **kw)

    @property
    def _package_requirement_parser(self):
        return [
            "package_height_required:height",
            "package_length_required:length",
            "package_weight_required:shipping_weight",
            "package_width_required:width",
        ]
