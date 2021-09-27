# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields, models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    lot_expiration_date = fields.Datetime(
        string="End of Expiration Date", related="lot_id.expiration_date"
    )

    def action_select_move_line(self):
        """Set the move line as the current one at the picking level."""
        self.ensure_one()
        self.picking_id.reception_screen_id.button_reset()
        self.picking_id.reception_screen_id.current_move_line_id = self
        self.picking_id.reception_screen_id.current_move_id = self.move_id
        self.picking_id.reception_screen_id.next_step()
        # FIXME: don't know how to close the pop-up and refresh the screen
        return self.picking_id.action_reception_screen_open()

    def action_reception_screen_open(self):
        """Open reception screen from specific move line."""
        self.picking_id.action_reception_screen_open()
        return self.action_select_move_line()
