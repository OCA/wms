# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from odoo.addons.component.core import Component


class SearchAction(Component):
    _inherit = "shopfloor.search.action"

    @property
    def _barcode_type_handler(self):
        res = super(SearchAction, self)._barcode_type_handler
        res["dock"] = self.dock_from_scan
        return res

    def dock_from_scan(self, barcode):
        model = self.env["stock.dock"]
        if not barcode:
            return model.browse()
        return model.search([("barcode", "=", barcode)], limit=1)
