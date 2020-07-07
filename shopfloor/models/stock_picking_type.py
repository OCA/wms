from odoo import fields, models


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    shopfloor_menu_ids = fields.Many2many(
        comodel_name="shopfloor.menu", string="Shopfloor Menus", readonly=True,
    )
    shopfloor_zero_check = fields.Boolean(
        string="Activate Zero Check",
        help="For Shopfloor scenarios using it (Cluster Picking, Zone Picking,"
        " Discrete order Picking), the zero check step will be activated when"
        " a location becomes empty after a move.",
    )
