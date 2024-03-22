# Copyright 2024 Foodles (http://www.foodles.co).
# @author Pierre Verkest <pierreverkest84@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockServiceLevel(models.Model):
    _inherit = "stock.service.level"

    route_ids = fields.Many2many(
        string="Routes",
        comodel_name="stock.location.route",
        domain="[('service_level_selectable', '=', True)]",
        help=(
            "Routes restricted to this service level. "
            "To get the route available in this list "
            "first turn on service_level_selectable on the route."
        ),
    )
