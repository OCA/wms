# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import api, fields, models


class ShopfloorProfile(models.Model):
    _name = "shopfloor.profile"
    _description = "Shopfloor profile settings"

    name = fields.Char(required=True)
    warehouse_id = fields.Many2one(
        "stock.warehouse",
        required=True,
        default=lambda self: self._default_warehouse_id(),
    )
    menu_ids = fields.Many2many(
        "shopfloor.menu", string="Menus", help="Menus visible for this profile"
    )
    active = fields.Boolean(default=True)

    @api.model
    def _default_warehouse_id(self):
        wh = self.env["stock.warehouse"].search([])
        if len(wh) == 1:
            return wh
