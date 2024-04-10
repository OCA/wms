# Copyright 2022 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.addons.component.core import Component

from ..config import MAPPING_AI_TO_TYPE, MAPPING_TYPE_TO_AI
from ..utils import GS1Barcode


class SearchAction(Component):
    _inherit = "shopfloor.search.action"

    def _search_type_to_gs1_ai(self, _type):
        """Convert search type to AIs.

        Each type can be mapped to multiple AIs.
        For instance, you can search a product by barcode (01) or manufacturer code (240).
        """
        return MAPPING_TYPE_TO_AI.get(_type)

    def _gs1_ai_to_search_type(self, ai):
        """Convert back GS1 AI to search type."""
        return MAPPING_AI_TO_TYPE[ai]

    def find(self, barcode, types=None, handler_kw=None):
        barcode = barcode or ""
        # Try to find records via GS1 and fallback to normal search
        res = self._find_gs1(barcode, types=types)
        if res:
            return res
        return super().find(barcode, types=types, handler_kw=handler_kw)

    def _find_gs1(self, barcode, types=None, handler_kw=None, safe=True):
        types = types or ()
        ai_whitelist = ()
        # Collect all AIs by converting from search types
        for _type in types:
            ai = self._search_type_to_gs1_ai(_type)
            if ai:
                ai_whitelist += ai
        if types and not ai_whitelist:
            # A specific type was asked but no AI could be found.
            return
        parsed = GS1Barcode.parse(barcode, ai_whitelist=ai_whitelist, safe=safe)
        # Return the 1st record found if parsing was successful
        for item in parsed:
            record = self.generic_find(
                item.value,
                types=(self._gs1_ai_to_search_type(item.ai),),
                handler_kw=handler_kw,
            )
            if record:
                return record
