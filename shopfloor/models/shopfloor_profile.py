# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class ShopfloorProfile(models.Model):
    _name = "shopfloor.profile"
    _description = "Shopfloor profile settings"

    name = fields.Char(required=True)
    menu_ids = fields.Many2many(
        "shopfloor.menu", string="Menus", help="Menus visible for this profile"
    )
    active = fields.Boolean(default=True)
