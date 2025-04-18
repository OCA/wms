# Copyright 2023 Camptocamp SA (http://www.camptocamp.com)
# Copyright 2025 ACSONE SA/NV (https://acsone.eu)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import api, fields, models


class ShopfloorMenu(models.Model):
    _inherit = "shopfloor.menu"

    set_product_barcode_is_possible = fields.Boolean(
        compute="_compute_set_product_barcode_is_possible"
    )
    set_product_barcode = fields.Boolean(
        string="Set product barcode",
        default=False,
        help="If for the product being processed, its related "
        "barcode is not set, ask to fill them up.",
    )

    @api.depends("scenario_id")
    def _compute_set_product_barcode_is_possible(self):
        for menu in self:
            menu.set_product_barcode_is_possible = menu.scenario_id.has_option(
                "set_product_barcode"
            )
