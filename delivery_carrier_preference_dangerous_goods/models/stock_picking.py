# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import models


class StockPicking(models.Model):

    _inherit = "stock.picking"

    def _carrier_valid(self, carrier):
        """Hook to add extra validation between carrier and picking"""
        res = super()._carrier_valid(carrier)
        if carrier.dangerous_goods_warning and self.contains_dangerous_goods:
            return False
        return res
