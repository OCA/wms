# Copyright 2024 Foodles (https://www.foodles.co)
# @author Pierre Verkest <pierreverkest84@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import api, fields, models


class Route(models.Model):
    _inherit = "stock.location.route"

    service_level_selectable = fields.Boolean(
        string="Service level",
        default=False,
        help=(
            "What ever we should apply service level restriction. "
            "This boolean as impact in the route selection because "
            "no service level defined means only stock.move without service "
            "level. Otherwise if this is not select it means ignore service level "
            "and route may apply on any case."
        ),
    )
    service_level_ids = fields.Many2many(
        string="Service levels",
        comodel_name="stock.service.level",
        store=True,
        readonly=False,
        compute="_compute_service_level_ids",
        help=(
            "Linking this route to service levels restrict the route for "
            "given service levels. If no service level set "
            "the route will be available only for stock.move without level service."
        ),
    )

    @api.depends("service_level_selectable")
    def _compute_service_level_ids(self):
        for route in self:
            if route.service_level_selectable:
                route.service_level_ids = route.service_level_ids
            else:
                route.service_level_ids = False
