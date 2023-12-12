# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    is_full_location_reservation_visible = fields.Boolean(
        "Is full location reservation visible",
        help="""If this is checked, the full reservation of a the picking is visible""",
    )
    merge_move_for_full_location_reservation = fields.Boolean(
        help="""If this is checked, the full reservation of a the picking will be done
            resulting of only one move (original one + full reservation one).
            WARNING: If checked, it will be impossible to get the original move back.
        """,
    )
