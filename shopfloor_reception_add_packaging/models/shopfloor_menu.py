# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ShopfloorMenu(models.Model):

    _inherit = "shopfloor.menu"

    create_new_packaging_is_possible = fields.Boolean(
        compute="_compute_create_new_packaging_is_possible"
    )
    create_new_packaging = fields.Boolean(
        help="Add a button to create a new packaging " "in 'set_quantity' screen."
    )

    @api.depends("scenario_id")
    def _compute_create_new_packaging_is_possible(self):
        for menu in self:
            menu.create_new_packaging_is_possible = menu.scenario_id.has_option(
                "create_new_packaging"
            )
