# Copyright 2025 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _compute_unrelease_allowed(self):
        # Prevent to unrelease a move loaded in a shipment advice
        loaded = self.browse()
        for move in self:
            if any(ml.shipment_advice_id and ml.qty_done for ml in move.move_line_ids):
                loaded |= move
        loaded.unrelease_allowed = False
        super(StockMove, self - loaded)._compute_unrelease_allowed()
