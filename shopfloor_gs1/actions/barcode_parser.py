# Copyright 2022 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.component.core import Component
from odoo.addons.shopfloor.actions.barcode_parser import BarcodeResult

from ..config import MAPPING_AI_TO_TYPE
from ..utils import GS1Barcode


class BarcodeParser(Component):
    """
    Some barcodes can have complex data structure
    """

    _inherit = "shopfloor.barcode.parser"

    def parse(self, barcode):
        """
        This method will parse the barcode and return the
        value with its type if determined.

        Override this to implement specific parsing

        """
        # Retrieve in any case the 'unknown' parsing with raw barcode
        result = super().parse(barcode)
        if not barcode:
            return result

        parsed = GS1Barcode.parse(barcode)
        for parsed_item in parsed:
            if _type := MAPPING_AI_TO_TYPE.get(parsed_item.ai):
                result[_type] = BarcodeResult(
                    type=_type,
                    value=parsed_item.value,
                    raw=parsed_item.raw_value,
                )
        return result
