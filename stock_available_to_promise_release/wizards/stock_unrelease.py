# Copyright 2023 ACSONE SA/NV (https://www.acsone.eu)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import models


class StockUnRelease(models.TransientModel):
    _name = "stock.unrelease"
    _description = "Stock Allocations Un Release"

    def unrelease(self):
        model = self.env.context.get("active_model")
        if model not in ("stock.move", "stock.picking"):
            return
        records = (
            self.env[model].browse(self.env.context.get("active_ids", [])).exists()
        )
        records.unrelease(safe_unrelease=True)
        return {"type": "ir.actions.act_window_close"}
