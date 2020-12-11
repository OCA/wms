# Copyright 2019 Camptocamp (https://www.camptocamp.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import models


class StockRelease(models.TransientModel):
    _name = "stock.release"
    _description = "Stock Allocations Release"

    def release(self):
        model = self.env.context.get("active_model")
        if model not in ("stock.move", "stock.picking"):
            return
        records = (
            self.env[model].browse(self.env.context.get("active_ids", [])).exists()
        )
        records.release_available_to_promise()
        return {"type": "ir.actions.act_window_close"}
