# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models


class StockQuant(models.Model):
    _inherit = "stock.quant"

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

    def _is_inventory_mode(self):
        """Used to control whether a quant was written on or created during an
        "inventory session", meaning a mode where we need to create the stock.move
        record necessary to be consistent with the `inventory_quantity` field.
        """
        # The default method check if we have the stock.group_stock_manager
        # group, however, we want to force using this mode from shopfloor
        # (cluster picking) when sudo is used and the user is a stock user.
        if self.env.context.get("inventory_mode") is True and self.env.su:
            return True
        return super()._is_inventory_mode()
