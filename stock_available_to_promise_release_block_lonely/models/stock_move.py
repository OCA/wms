# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockMove(models.Model):

    _inherit = "stock.move"

    def _blocked_on_backorder(self):
        res = super()._blocked_on_backorder()

        ...

        return res
