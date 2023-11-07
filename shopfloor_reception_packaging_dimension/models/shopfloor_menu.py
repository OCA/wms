# Copyright 2023 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import api, fields, models


class ShopfloorMenu(models.Model):
    _inherit = "shopfloor.menu"

    set_packaging_dimension_is_possible = fields.Boolean(
        compute="_compute_set_packaging_dimension_is_possible"
    )
    set_packaging_dimension = fields.Boolean(
        string="Set packaging dimension",
        default=False,
        help="If for the product being processed, its related packaging "
        "dimension are not set, ask to fill them up.",
    )

    @api.depends("scenario_id")
    def _compute_set_packaging_dimension_is_possible(self):
        for menu in self:
            menu.set_packaging_dimension_is_possible = menu.scenario_id.has_option(
                "set_packaging_dimension"
            )
