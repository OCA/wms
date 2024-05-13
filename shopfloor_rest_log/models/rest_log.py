# Copyright 2022 Camptocamp SA (http://www.camptocamp.com)
# @author Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
from odoo import fields, models


class RestLog(models.Model):
    _inherit = "rest.log"

    app_version = fields.Char()
    real_uid = fields.Many2one(
        comodel_name="res.users",
        string="Real user",
        help="Some services might use a different user in the environment. "
        "Whenever possible, this field will hold a reference to the real user doing the call. "
        "This information can be found in the header `App-User-Id`.",
    )
