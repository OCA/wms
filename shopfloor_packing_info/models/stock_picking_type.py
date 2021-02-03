# Copyright 2021 Camptocamp SA (https://www.camptocamp.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import fields, models


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    shopfloor_display_packing_info = fields.Boolean(
        string="Display customer packing info",
        help="For the Shopfloor Checkout/Packing scenarios to display the"
        " customer packing info.",
    )
