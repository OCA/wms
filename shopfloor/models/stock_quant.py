# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models


class StockQuant(models.Model):
    _inherit = "stock.quant"

    def _is_inventory_mode(self):
        """ Used to control whether a quant was written on or created during an
        "inventory session", meaning a mode where we need to create the stock.move
        record necessary to be consistent with the `inventory_quantity` field.
        """
        # The default method check if we have the stock.group_stock_manager
        # group, however, we want to force using this mode from shopfloor
        # (cluster picking) when sudo is used and the user is a stock user.
        if self.env.context.get("inventory_mode") is True and self.env.su:
            return True
        return super()._is_inventory_mode()
