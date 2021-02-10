# Copyright 2021 <raphael.reverdy@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _generate_serial_move_line_commands(self, lot_names, origin_move_line=None):
        locations = self.move_dest_ids.location_dest_id
        self = self.with_context(_pre_location_dest=locations)

        return super()._generate_serial_move_line_commands(
            lot_names, origin_move_line=origin_move_line
        )

    def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
        locations = self.move_dest_ids.location_dest_id
        self = self.with_context(_pre_location_dest=locations)

        return super()._prepare_move_line_vals(
            quantity=quantity, reserved_quant=reserved_quant
        )
