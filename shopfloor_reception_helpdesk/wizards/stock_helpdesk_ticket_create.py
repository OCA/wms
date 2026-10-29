# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockHelpdeskTicketCreate(models.TransientModel):
    _inherit = "stock.helpdesk.ticket.create"

    motive_id = fields.Many2one("helpdesk.ticket.motive")

    def _prepare_ticket_values(self) -> dict:
        res = super()._prepare_ticket_values()
        if self.env.context.get("from_shopfloor_reception"):
            res["is_shopfloor_created"] = True
            stock_move = self.env["stock.move"].browse(res.get("stock_move_id"))
            stock_picking = self.env["stock.picking"].browse(
                res.get("stock_picking_id")
            )
            product = self.env["product.product"].browse(res.get("product_id"))
            name_parts = [
                (stock_move or stock_picking).origin or stock_picking.name,
                self.motive_id.name,
                product.display_name,
            ]
            res["name"] = " - ".join(filter(None, name_parts))
        return res
