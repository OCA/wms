# Copyright 2022 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.addons.component.core import Component

from ..utils import GS1Barcode


class SearchAction(Component):
    _inherit = "shopfloor.search.action"

    def find(self, barcode, types=None, handler_kw=None):
        barcode = barcode or ""
        res = self._find_gs1(barcode, types=types)
        if res:
            return res
        return super().find(barcode, types=types, handler_kw=handler_kw)

    # TODO: add tests!!!!!!!
    def _find_gs1(self, barcode, types=None, handler_kw=None):
        types = types or ()
        ai_whitelist = [GS1Barcode.to_ai(x) for x in types if GS1Barcode.to_ai(x)]
        parsed = GS1Barcode.parse(barcode, ai_whitelist=ai_whitelist)
        for item in parsed:
            record = self.generic_find(
                item.value, types=(item.type,), handler_kw=handler_kw
            )
            if record:
                return record
