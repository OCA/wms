# Copyright 2022 Brian McMaster <brian@mcmpest.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
from odoo import fields, models


class ShopfloorApp(models.Model):
    _inherit = "shopfloor.app"

    use_default_profile = fields.Boolean(string="Set the user profile by default")

    def _make_app_info(self, demo=False):
        res = super()._make_app_info(demo)
        res["use_default_profile"] = self.use_default_profile
        return res
