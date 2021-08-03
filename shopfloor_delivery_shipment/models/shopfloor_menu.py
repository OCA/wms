# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from odoo import api, fields, models


class ShopfloorMenu(models.Model):
    _inherit = "shopfloor.menu"

    shipment_advice_create_is_possible = fields.Boolean(
        compute="_compute_shipment_advice_create_is_possible"
    )
    allow_shipment_advice_create = fields.Boolean(
        string="Allow Shipment Advice Creation",
        default=False,
        help="Some scenario may create shipment advice(s) automatically when a "
        "product or package is scanned and no shipment advice already exists. ",
    )

    @api.depends("scenario_id")
    def _compute_shipment_advice_create_is_possible(self):
        for menu in self:
            menu.shipment_advice_create_is_possible = menu.scenario_id.has_option(
                "allow_create_shipment_advice"
            )
