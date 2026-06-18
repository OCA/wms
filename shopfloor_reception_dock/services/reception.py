# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from odoo.addons.component.core import Component


class Reception(Component):
    _inherit = "shopfloor.reception"

    def _scan_document__get_handlers_by_type(self):
        res = super()._scan_document__get_handlers_by_type()
        res["dock"] = self._scan_document__by_dock
        return res

    def _scan_document__by_dock(self, dock, barcode):
        if not dock:
            return None

        pickings = self.env["stock.picking"].search(
            [
                *self._domain_stock_picking(),
                ("dock_ids", "in", dock.ids),
            ],
            order=self._order_stock_picking(),
        )

        if not pickings:
            return self._response_for_select_document(
                message=self.msg_store.dock_no_assigned_picking(dock)
            )

        if len(pickings) == 1:
            return self._select_picking(pickings)

        return self._response_for_select_document(
            pickings=pickings, message=self.msg_store.dock_pickings_filtered(dock)
        )
