# Copyright 2021 Camptocamp SA (https://www.camptocamp.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    shopfloor_packing_info_id = fields.Many2one(
        string="Packing information", related="partner_id.shopfloor_packing_info_id",
    )
    shopfloor_display_packing_info = fields.Boolean(
        related="picking_type_id.shopfloor_display_packing_info",
    )
