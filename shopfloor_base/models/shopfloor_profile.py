# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
from odoo import fields, models


class ShopfloorProfile(models.Model):
    _name = "shopfloor.profile"
    _description = "Shopfloor profile settings"

    name = fields.Char(required=True)
    menu_ids = fields.One2many(
        comodel_name="shopfloor.menu",
        inverse_name="profile_id",
        string="Menus",
        help="Menus visible for this profile",
    )
    active = fields.Boolean(default=True)
