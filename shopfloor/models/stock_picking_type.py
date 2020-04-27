from odoo import fields, models


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    shopfloor_menu_ids = fields.Many2many(
        comodel_name="shopfloor.menu", string="Shopfloor Menus", readonly=True,
    )
