# Copyright 2022 Brian McMaster <brian@mcmpest.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
from odoo import fields, models


class ShopfloorAppUserProfile(models.Model):
    _name = "shopfloor.app.user.profile"
    _description = "Stores a users default profile per shopfloor app"

    user_id = fields.Many2one("res.users", string="User")
    shopfloor_app_id = fields.Many2one("shopfloor.app", string="Shopfloor App")
    profile_id = fields.Many2one(
        "shopfloor.profile", string="Shopfloor Default Profile"
    )

    _sql_constraints = [
        (
            "unique_app_profile",
            "unique (user_id, shopfloor_app_id)",
            "A user can only have one default profile per shopfloor app",
        )
    ]
