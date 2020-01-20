from odoo import fields, models


class ShopfloorGroup(models.Model):
    _name = "shopfloor.group"
    _description = "Shopfloor group, governs which menu items are visible"

    name = fields.Char(required=True)
    user_ids = fields.Many2many("res.users", string="Members")
    menu_ids = fields.Many2many(
        'shopfloor.menu',
        string="Menus",
        help="Can see these menus",
    )
