# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import api, fields, models

AUTO_POST_LINE = """
When setting result pack & destination,
automatically post the corresponding line
if this option is checked.
"""


class ShopfloorMenu(models.Model):
    _inherit = "shopfloor.menu"

    auto_post_line = fields.Boolean(
        string="Automatically post line",
        default=False,
        help=AUTO_POST_LINE,
    )
    auto_post_line_is_possible = fields.Boolean(
        compute="_compute_auto_post_line_is_possible"
    )

    @api.depends("scenario_id")
    def _compute_auto_post_line_is_possible(self):
        for menu in self:
            menu.auto_post_line_is_possible = bool(
                menu.scenario_id.has_option("auto_post_line")
            )
