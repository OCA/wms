# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models


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
