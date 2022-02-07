# Copyright 2022 Camptocamp SA (http://www.camptocamp.com)
# @author Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
from odoo import fields, models

from ..utils import APP_VERSION


class ShopfloorApp(models.Model):
    _inherit = "shopfloor.app"

    app_version = fields.Char(compute="_compute_app_version")

    def _compute_app_version(self):
        # Override this to choose your own versioning policy
        for rec in self:
            rec.app_version = APP_VERSION
