# Copyright 2022 Akretion (http://www.akretion.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
from odoo import fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    shopfloor_default_profile_id = fields.Many2one(
        comodel_name="shopfloor.profile", string="Shopfloor default profile"
    )
