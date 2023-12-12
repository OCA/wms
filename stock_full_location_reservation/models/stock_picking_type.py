# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    is_full_location_reservation_visible = fields.Boolean(
        "Is full location reservation visible",
        help="""If this is checked, the full reservation of a the picking is visible""",
    )
