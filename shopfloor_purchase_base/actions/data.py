# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.addons.component.core import Component
from odoo.addons.shopfloor_base.utils import ensure_model


class DataAction(Component):
    _inherit = "shopfloor.data.action"

    def _get_purchase_order_parser(self, **kw):
        res = self._simple_record_parser()
        res += [
            "partner_ref",
        ]
        return res

    @ensure_model("purchase.order")
    def purchase_order(self, record, **kw):
        parser = self._get_purchase_order_parser(**kw)
        return self._jsonify(record, parser, **kw)

    def _get_picking_parser(self, record, **kw):
        parser = super()._get_picking_parser(record, **kw)
        if kw.get("with_purchase_order"):
            parser.append(
                ("purchase_id:purchase_order", self._get_purchase_order_parser(**kw))
            )
        return parser
