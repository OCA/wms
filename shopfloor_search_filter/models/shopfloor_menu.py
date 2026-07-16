# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ShopfloorMenu(models.Model):
    _inherit = "shopfloor.menu"

    allow_product_scan = fields.Boolean(
        default=True,
        help=(
            "Allow identifying items by scanning product barcodes or "
            "internal references."
        ),
    )
    allow_package_scan = fields.Boolean(
        default=True,
        help=(
            "Allow identifying stock packages (containers/pallets) by "
            "scanning their package names."
        ),
    )
    allow_picking_scan = fields.Boolean(
        default=True,
        help=(
            "Allow finding a warehouse transfer document by scanning its "
            "name or source document number."
        ),
    )
    allow_location_scan = fields.Boolean(
        default=True,
        help=(
            "Allow scanning a stock location barcode or name to identify "
            "the area to work on."
        ),
    )
    allow_lot_scan = fields.Boolean(
        default=True,
        help=("Allow scanning lot numbers to identify lot-tracked " "products."),
    )
    allow_packaging_scan = fields.Boolean(
        default=True,
        help=(
            "Allow scanning box, crate, or pallet barcodes linked to a "
            "specific product to calculate quantities automatically."
        ),
    )
