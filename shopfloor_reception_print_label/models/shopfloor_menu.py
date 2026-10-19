# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ShopfloorMenu(models.Model):
    _inherit = "shopfloor.menu"

    auto_print_labels_on_location_scan = fields.Boolean(
        help="When True, scanning a location during the 'set quantity' "
        "will automatically print labels"
    )
