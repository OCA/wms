# Copyright 2022 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.component.core import Component
from odoo.addons.shopfloor.actions.barcode_parser import BarcodeResult

from ..config import MAPPING_AI_TO_TYPE, MAPPING_TYPE_TO_AI
from ..utils import GS1Barcode


class BarcodeParser(Component):
    """
    Some barcodes can have complex data structure
    """

    _inherit = "shopfloor.barcode.parser"

    def _search_type_to_gs1_ai(self, _type):
        """Convert search type to AIs.

        Each type can be mapped to multiple AIs.
        For instance, you can search a product by barcode (01) or manufacturer code (240).
        """
        return MAPPING_TYPE_TO_AI.get(_type)

    def _gs1_ai_to_search_type(self, ai):
        """Convert back GS1 AI to search type."""
        return MAPPING_AI_TO_TYPE[ai]

    def _parse_gs1(self, barcode, types, safe=True):
        types = types or ()
        ai_whitelist = ()
        # Collect all AIs by converting from search types
        for _type in types:
            ai = self._search_type_to_gs1_ai(_type)
            if ai:
                ai_whitelist += ai
        if types and not ai_whitelist:
            # A specific type was asked but no AI could be found.
            return None, None
        parsed = GS1Barcode.parse(barcode, ai_whitelist=ai_whitelist, safe=safe)
        return parsed

    def parse(self, barcode, types):
        """
        This method will parse the barcode and return the
        value with its type if determined.

        Override this to implement specific parsing

        """
        # search = self._actions_for("search")
        parsed = self._parse_gs1(barcode, types)
        if parsed:
            result = []
            for barcode_type in self.search_action._barcode_type_handler.keys():
                for parsed_item in parsed:
                    if parsed_item.ai in MAPPING_TYPE_TO_AI.get(barcode_type, tuple()):
                        result.append(
                            BarcodeResult(
                                type=barcode_type,
                                value=parsed_item.value,
                                raw=parsed_item.raw_value,
                            )
                        )
            if result:
                return result
        return super().parse(barcode, types)
