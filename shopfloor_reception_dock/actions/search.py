# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from odoo.addons.component.core import Component


class SearchAction(Component):
    _inherit = "shopfloor.search.action"

    @property
    def _barcode_type_handler(self):
        res = super(SearchAction, self)._barcode_type_handler
        res["dock"] = self._find_dock
        return res

    def dock_from_scan(self, barcode):
        res = self.find(barcode, types=["dock"])
        return res.record if res else self.env["stock.dock"].browse()

    def _find_dock(self, parse_results, btype="dock"):
        model = self.env["stock.dock"]
        barcode = self._get_parse_results_value(parse_results, btype)
        if not barcode:
            return model.browse()
        return model.search([("barcode", "=", barcode)], limit=self._limit)
