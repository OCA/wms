# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from odoo.addons.component.core import Component


class SearchAction(Component):
    _inherit = "shopfloor.search.action"

    @property
    def _barcode_type_handler(self):
        res = super(SearchAction, self)._barcode_type_handler
        res["grn"] = self._find_grn
        return res

    def grn_from_scan(self, barcode):
        res = self.find(barcode, types=["grn"])
        return res.record if res else self.env["stock.grn"].browse()

    def _find_grn(self, parse_results, btype="grn"):
        model = self.env["stock.grn"]
        barcode = self._get_parse_results_value(parse_results, btype)
        if not barcode:
            return model.browse()
        res = model.search([("name", "=", barcode)], limit=self._limit)
        return res
