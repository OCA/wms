# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.addons.barcodes_gtin.tools.barcode_validation import is_valid_gtin_barcode
from odoo.addons.component.core import Component
from odoo.addons.shopfloor.actions.barcode_parser import BarcodeResult


class BarcodeParser(Component):
    _inherit = "shopfloor.barcode.parser"

    def parse(self, barcode):
        result = super().parse(barcode)

        if is_valid_gtin_barcode(barcode):
            result.update(
                {
                    "product": BarcodeResult(
                        type="product",
                        value=barcode[1:]
                        if len(barcode) == 14 and barcode.startswith("0")
                        else barcode,
                        raw=barcode,
                    )
                }
            )

        return result
