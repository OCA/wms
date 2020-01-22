from odoo import fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    # in practice, it's a one2one
    shopfloor_profile_ids = fields.One2many(
        comodel_name="shopfloor.profile", inverse_name="user_id", readonly=True
    )
