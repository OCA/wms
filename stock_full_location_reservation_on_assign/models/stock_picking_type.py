# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    auto_full_location_reservation_on_assign = fields.Boolean(
        "Auto full location reservation on assign",
        help="If this is checked, the full reservation "
        "will be automatically triggered on aciton_assign",
    )
