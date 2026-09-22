# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo.addons.component.core import Component

from ..tools.barcodes_gtin import get_gtin_variants


class SearchAction(Component):
    _inherit = "shopfloor.search.action"

    def _find_product_domain_barcodes(self, barcode):
        barcodes = super()._find_product_domain_barcodes(barcode)
        if variants := get_gtin_variants(barcode):
            barcodes.extend(x for x in variants if x not in barcodes)
        return barcodes
