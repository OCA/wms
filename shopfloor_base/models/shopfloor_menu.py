# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# Copyright 2021 ACSONE SA/NV (http://www.camptocamp.com)
# @author Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class ShopfloorMenu(models.Model):
    _name = "shopfloor.menu"
    _description = "Menu displayed in the scanner application"
    _order = "sequence"

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer()
    profile_id = fields.Many2one(
        "shopfloor.profile", string="Profile", help="Visible on this profile only"
    )
    scenario_id = fields.Many2one(
        comodel_name="shopfloor.scenario", required=True, ondelete="cascade"
    )
    scenario = fields.Char(related="scenario_id.key")
    active = fields.Boolean(default=True)
