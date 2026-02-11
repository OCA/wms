# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component
from odoo.addons.shopfloor_base.utils import ensure_model


class DataAction(Component):
    _inherit = "shopfloor.data.action"

    @property
    def _product_parser(self):
        """
        The jsonifier engine passes (record, field_name) when calling
        parser functions. We use *args to capture them.
        """
        res = super(DataAction, self)._product_parser
        return res + ["use_expiration_date"]

    @ensure_model("stock.move.line")
    def move_line(self, record, with_picking=False, **kw):
        data = super().move_line(record, with_picking, **kw)

        lot_data = {}
        if lot := kw.get("lot"):
            lot_data = self._jsonify(lot, self._lot_parser)
        elif lot_name := kw.get("lot_name"):
            lot_data["name"] = lot_name

        if lot_data:
            data["lot"] = data.get("lot") or {}
            data["lot"].update(lot_data)

        return data
