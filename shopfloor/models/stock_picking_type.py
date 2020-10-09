# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import api, fields, models


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
    shopfloor_display_packing_info = fields.Boolean(
        string="Display customer packing info",
        help="For the Shopfloor Checkout/Packing scenarios to display the"
        " customer packing info.",
    )

    @api.constrains("show_entire_packs")
    def _check_move_entire_packages(self):
        menu_items = self.env["shopfloor.menu"].search(
            [("picking_type_ids", "in", self.ids)]
        )
        menu_items._check_move_entire_packages()
