# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import api, fields, models


class StockInventory(models.Model):
    _inherit = "stock.inventory"

    shopfloor_validated = fields.Boolean(
        string="To validate",
        help="Shopfloor doesn't validate the inventory at the end of the process. "
        "The manager can do it manually.",
        tracking=True,
        copy=False,
    )
    inventory_line_count = fields.Integer(
        compute="_compute_inventory_info",
        help="Technical field. Indicates number of lines included.",
    )

    @api.depends("line_ids", "sub_location_ids")
    def _compute_inventory_info(self):
        for item in self:
            item.inventory_line_count = len(item.line_ids)
