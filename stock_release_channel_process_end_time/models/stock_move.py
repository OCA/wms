# Copyright 2024 ACSONE SA/NV (https://acsone.eu)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _prepare_procurement_values(self):
        values = super()._prepare_procurement_values()
        if (
            self.picking_id.picking_type_code == "outgoing"
            and self.picking_id.release_channel_id.process_end_date
            and bool(
                self.env["ir.config_parameter"]
                .sudo()
                .get_param(
                    "stock_release_channel_process_end_time.stock_release_use_channel_end_date"
                )
            )
        ):
            values[
                "date_deadline"
            ] = self.picking_id.release_channel_id.process_end_date
        return values
