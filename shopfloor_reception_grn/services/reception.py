# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)


from datetime import timezone

from odoo.osv import expression

from odoo.addons.component.core import Component

UTC = timezone.utc


class Reception(Component):
    _inherit = "shopfloor.reception"

    def _scan_document__get_handlers_by_type(self):
        res = super()._scan_document__get_handlers_by_type()
        res["grn"] = self._scan_document__by_grn
        return res

    def _scan_document__by_grn(self, grn, barcode):
        if not grn:
            return None

        pickings = self.env["stock.picking"].search(
            expression.AND([self._domain_stock_picking(), [("grn_id", "in", grn.ids)]]),
            order=self._order_stock_picking(),
        )

        if not pickings:
            return self._response_for_select_document(
                message=self.msg_store.no_picking_found_for_grn(grn)
            )

        if len(pickings) == 1:
            return self._select_picking(pickings)

        return self._response_for_select_document(
            pickings=pickings, message=self.msg_store.grn_pickings_filtered(grn)
        )
