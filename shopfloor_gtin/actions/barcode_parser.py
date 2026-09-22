# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.addons.component.core import Component
from odoo.addons.shopfloor.actions.barcode_parser import BarcodeResult

from ..tools.barcodes_gtin import is_valid_gtin_barcode


class BarcodeParser(Component):
    _inherit = "shopfloor.barcode.parser"

    def parse(self, barcode):
        result = super().parse(barcode)

        if is_valid_gtin_barcode(barcode):
            result.update(
                {
                    "product": BarcodeResult(
                        type="product",
                        value=barcode,
                        raw=barcode,
                    )
                }
            )

        return result
