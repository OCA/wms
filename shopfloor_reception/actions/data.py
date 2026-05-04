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

    @property
    def _lot_parser_reception(self):
        return self._simple_record_parser() + [
            "ref",
            (
                "expiration_date",
                lambda rec, fname:
                # Odoo Datetime fields are stored as naive UTC in the DB.
                rec.expiration_date.isoformat() + "+00:00"
                if rec.expiration_date
                else None,
            ),
        ]

    @ensure_model("stock.move.line")
    def move_line(self, record, with_picking=False, **kw):
        data = super().move_line(record, with_picking, **kw)

        lot_data = {}
        if lot := kw.get("lot"):
            lot_data = self._jsonify(lot, self._lot_parser_reception)
            # add expiration_date from scan if not defined on existing lot
            if not lot_data.get("expiration_date") and (
                lot_expiration_date := kw.get("lot_expiration_date")
            ):
                lot_data["expiration_date"] = lot_expiration_date.isoformat()
        else:
            if lot_name := kw.get("lot_name"):
                lot_data["name"] = lot_name
            if lot_expiration_date := kw.get("lot_expiration_date"):
                lot_data["expiration_date"] = lot_expiration_date.isoformat()

        if lot_data:
            data["lot"] = data.get("lot") or {}
            data["lot"].update(lot_data)

        return data
