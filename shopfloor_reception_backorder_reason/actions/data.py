# Copyright 2025 ACSONE SA/NV (https://acsone.eu)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)


from odoo.addons.component.core import Component
from odoo.addons.shopfloor_base.utils import ensure_model


class DataAction(Component):
    _inherit = "shopfloor.data.action"

    @property
    def _backorder_reason_parser(self, **kw):
        return [
            "id",
            "name",
            (
                "backorder_action_to_do",
                lambda rec, fname: {
                    "action": rec.backorder_action_to_do,
                    "label": "".join(
                        [
                            field_value[1]
                            for field_value in rec._fields[
                                "backorder_action_to_do"
                            ]._description_selection(rec.env)
                            if field_value[0] == rec.backorder_action_to_do
                        ]
                    ),
                },
            ),
        ]

    def _get_backorder_reason_parser(self, record, **kw):
        parser = self._backorder_reason_parser
        return parser

    @ensure_model("stock.backorder.reason")
    def backorder_reason(self, record, **kw):
        return self._jsonify(
            record, self._get_backorder_reason_parser(record, **kw), **kw
        )

    def backorder_reasons(self, record, **kw):
        return self.backorder_reason(record, multi=True)
