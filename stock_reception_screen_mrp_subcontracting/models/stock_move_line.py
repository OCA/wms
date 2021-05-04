# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    def unlink(self):
        # Overridden to not unlink lines of finished products moves
        # if the context key 'subcontracting_skip_unlink' is set
        if self.env.context.get("subcontracting_skip_unlink"):
            return False
        return super().unlink()
