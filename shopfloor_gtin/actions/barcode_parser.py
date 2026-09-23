# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.addons.component.core import Component
from odoo.addons.shopfloor.actions.barcode_parser import BarcodeResult

from ..tools.barcodes_gtin import parse_gtin


class BarcodeParser(Component):
    _inherit = "shopfloor.barcode.parser"

    def parse(self, barcode):
        result = super().parse(barcode)

        if parsed_barcode := parse_gtin(barcode):
            result.update(
                {
                    "product": BarcodeResult(
                        type="product",
                        value=parsed_barcode.value,
                        raw=barcode,
                    )
                }
            )

        return result
