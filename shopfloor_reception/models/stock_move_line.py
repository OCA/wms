# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

from odoo import models


class StockMoveLine(models.Model):

    _inherit = "stock.move.line"

    @property
    def shopfloor_should_create_lot(self) -> bool:
        """
        This will return True if the line should be used to create lots
        """
        return bool(
            (not self.lot_id and not self.lot_name)
            and self.picking_type_use_create_lots
        )
