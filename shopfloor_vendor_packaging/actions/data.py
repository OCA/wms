# Copyright 2024 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.component.core import Component
from odoo.addons.shopfloor_base.utils import ensure_model


class DataAction(Component):
    _inherit = "shopfloor.data.action"

    @ensure_model("stock.move.line")
    def move_line(self, record, with_picking=False, **kw):
        display_vendor_packaging = kw.get("display_vendor_packaging")
        record = record.with_context(
            display_vendor_packaging=display_vendor_packaging,
        )
        return super().move_line(record, with_picking, **kw)

    @ensure_model("stock.move")
    def move(self, record, **kw):
        display_vendor_packaging = kw.get("display_vendor_packaging")
        record = record.with_context(
            display_vendor_packaging=display_vendor_packaging,
        )
        return super().move(record, **kw)

    @ensure_model("stock.package_level")
    def package_level(self, record, **kw):
        display_vendor_packaging = kw.get("display_vendor_packaging")
        record = record.with_context(display_vendor_packaging=display_vendor_packaging)
        return super().package_level(record, **kw)

    @ensure_model("product.product")
    def product(self, record, **kw):
        display_vendor_packaging = kw.get("display_vendor_packaging")
        record = record.with_context(display_vendor_packaging=display_vendor_packaging)
        return super().product(record, **kw)

    def _product_packaging(self, rec, field):
        display_vendor_packaging = rec.env.context.get("display_vendor_packaging")
        packagings = rec.packaging_ids
        if display_vendor_packaging:
            packagings = packagings.filtered(lambda x: x.qty)
        else:
            packagings = packagings.filtered(
                lambda x: x.qty and not x.packaging_type_id.is_vendor_packaging
            )
        return self._jsonify(
            packagings,
            self._packaging_parser,
            multi=True,
        )
