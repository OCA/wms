# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from odoo.addons.component.core import Component
from odoo.addons.shopfloor_base.utils import ensure_model


class DataDetailAction(Component):
    _inherit = "shopfloor.data.detail.action"

    @ensure_model("shipment.advice")
    def shipment_advice_detail(self, record, **kw):
        data = self._jsonify(
            record.with_context(shipment_advice=record.id),
            self._shipment_advice_detail_parser,
            **kw
        )
        data["is_planned"] = bool(record.planned_move_ids)
        return data

    @property
    def _shipment_advice_detail_parser(self):
        return self._shipment_advice_parser + [
            (
                "planned_move_ids:planned_moves",
                lambda record, fname: self.moves(record[fname]),
            )
        ]
