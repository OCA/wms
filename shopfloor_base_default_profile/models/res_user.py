# Copyright 2022 Brian McMaster <brian@mcmpest.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
from odoo import fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    shopfloor_default_profile_ids = fields.One2many(
        "shopfloor.app.user.profile", "user_id", string="Shopfloor App Default Profiles"
    )
