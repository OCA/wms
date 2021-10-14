# Copyright 2021 Camptocamp SA (http://www.camptocamp.com)
# @author Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
from odoo import fields, models


class ShopfloorApp(models.Model):
    """Backend for a Shopfloor app."""

    _name = "shopfloor.app"
    _inherit = "collection.base"
    _description = "A Shopfloor application"

    # TODO: attach and load menu items and other records
    # from the specific shopfloor.app (aka current collection)
    name = fields.Char(required=True, translate=True)
    short_name = fields.Char(required=True, translate=True)
    # Unique name
    tech_name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    api_route = fields.Char(
        compute="_compute_api_route",
        help="Base route for endpoints attached to this app.",
    )
    url = fields.Char(compute="_compute_url", help="Public URL to use the app.")

    _sql_constraints = [("tech_name", "unique(tech_name)", "tech_name must be unique")]

    _api_route_path = "/shopfloor/"

    def _compute_api_route(self):
        for rec in self:
            rec.api_route = rec._api_route_path + rec.tech_name

    _base_url_path = "/shopfloor/app/"

    def _compute_url(self):
        for rec in self:
            rec.url = rec._base_url_path + rec.tech_name

    def action_open_app(self):
        return {
            "type": "ir.actions.act_url",
            "name": self.name,
            "url": self.url,
            "target": "new",
        }
