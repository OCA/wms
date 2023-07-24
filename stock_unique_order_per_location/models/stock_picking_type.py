# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import fields, models


class StockPickingType(models.Model):

    _inherit = "stock.picking.type"

    same_next_picking = fields.Boolean(
        string="Do not mix sources at destination",
        help="When checked, the destination location must either be empty or "
        "contain stock reserved only by the next picking. This ensures that you "
        "do not mix different sales order on the destination location",
    )
