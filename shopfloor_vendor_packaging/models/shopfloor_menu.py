# Copyright 2024 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models

DISPLAY_VENDOR_PACKAGING_HELP = """
    When enabled, the user will be able to see the vendor packagings
    in the frontend, e.g. in the qty picker.
"""


class ShopfloorMenu(models.Model):
    _inherit = "shopfloor.menu"

    display_vendor_packaging = fields.Boolean(
        string="Display vendor packagings",
        default=False,
        help=DISPLAY_VENDOR_PACKAGING_HELP,
    )
    display_vendor_packaging_is_possible = fields.Boolean(
        compute="_compute_display_vendor_packaging_is_possible",
    )

    @api.depends("scenario_id")
    def _compute_display_vendor_packaging_is_possible(self):
        for menu in self:
            menu.display_vendor_packaging_is_possible = menu.scenario_id.has_option(
                "display_vendor_packaging"
            )
