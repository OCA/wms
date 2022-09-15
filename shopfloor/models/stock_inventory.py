# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import api, fields, models


class StockInventory(models.Model):
    _inherit = "stock.inventory"

    def user_has_groups(self, groups):
        if self.env.context.get("_sf_inventory"):
            allow_groups = groups.split(",")
            # action_validate checks if the user is a manager, but
            # in shopfloor, we want to programmatically create and
            # validate inventories under the hood. sudo sets the su
            # flag but not the group: allow to bypass the check when
            # sudo is used.
            if "stock.group_stock_manager" in allow_groups and self.env.su:
                return True
        return super().user_has_groups(groups)

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
