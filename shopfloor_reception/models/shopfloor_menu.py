# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
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
    auto_post_line_is_possible = fields.Boolean(compute="_compute_scenario_options")

    select_move_by_click = fields.Boolean(
        string="Select move by click",
        default=False,
        help="If this option is checked: "
        "The moves are selectable by a user click, "
        "this means you don't have to scan a barcode",
    )
    select_move_by_click_is_possible = fields.Boolean(
        compute="_compute_scenario_options"
    )

    @api.depends("scenario_id")
    def _compute_scenario_options(self):
        for menu in self:
            menu.auto_post_line_is_possible = bool(
                menu.scenario_id.has_option("auto_post_line")
            )
            menu.select_move_by_click_is_possible = bool(
                menu.scenario_id.has_option("select_move_by_click")
            )
