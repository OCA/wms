# Copyright 2021 Camptocamp SA (http://www.camptocamp.com)
# @author Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
from functools import partial

from odoo import api, fields, models

from odoo.addons.base_rest.controllers.main import RestController
from odoo.addons.base_rest.tools import _inspect_methods


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
    auth_type = fields.Selection(
        selection="_selection_auth_type", default="user_endpoint"
    )

    _sql_constraints = [("tech_name", "unique(tech_name)", "tech_name must be unique")]

    _api_route_path = "/shopfloor/"

    def _compute_api_route(self):
        for rec in self:
            rec.api_route = rec._api_route_path + rec.tech_name

    _base_url_path = "/shopfloor/app/"

    def _compute_url(self):
        for rec in self:
            rec.url = rec._base_url_path + rec.tech_name

    def _selection_auth_type(self):
        return self.env["endpoint.route.handler"]._selection_auth_type()

    def action_open_app(self):
        return {
            "type": "ir.actions.act_url",
            "name": self.name,
            "url": self.url,
            "target": "new",
        }

    # TODO: move to shopfloor_app_base? or just `app_base`?
    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for rec in res:
            rec._register_endpoints()
        return res

    def write(self, vals):
        res = super().write(vals)
        if any([x in vals for x in self._endpoint_impacting_fields()]):
            for rec in self:
                rec._register_endpoints()
        return res

    def _endpoint_impacting_fields(self):
        return ["tech_name"]

    def unlink(self):
        for rec in self:
            rec._unregister_endpoints()
        return super().unlink()

    def _register_hook(self):
        super()._register_hook()
        for rec in self.search([]):
            rec._register_endpoints()

    def _register_endpoints(self):
        services = self._get_services()
        for service in services:
            self._prepare_non_decorated_endpoints(service)
            self._generate_endpoints(service)

    def _unregister_endpoints(self):
        registry = self.env["endpoint.route.handler"]._endpoint_registry
        for key, __ in registry.get_rules_by_group(self._route_group()):
            registry.drop_rule(key)

    def _prepare_non_decorated_endpoints(self, service):
        # Autogenerate routing info where missing
        self.env["rest.service.registration"]._prepare_non_decorated_endpoints(service)

    def _generate_endpoints(self, service):
        rest_endpoint_handler = RestController()._process_method
        values = self._generate_endpoints_values(service, self.api_route)
        for vals in values:
            self._generate_endpoints_routes(service, rest_endpoint_handler, vals)
            self.env["rest.service.registration"]._register_rest_route(
                self.api_route_public
            )

    def _generate_endpoints_values(self, service, api_route):
        values = []
        root_path = self.api_route.rstrip("/") + "/" + service._usage
        for name, method in _inspect_methods(service.__class__):
            if not hasattr(method, "routing"):
                continue
            routing = method.routing
            for routes, http_method in routing["routes"]:
                method_name = "{}_{}".format(http_method.lower(), name)
                default_route = root_path + "/" + routes[0].lstrip("/")
                route_params = dict(
                    route=["{}{}".format(root_path, r) for r in routes],
                    methods=[http_method],
                )
                # TODO: get this params from self?
                for attr in {"auth", "cors", "csrf", "save_session"}:
                    if attr in routing:
                        route_params[attr] = routing[attr]
                # {'route': ['/foo/testing/app/user_config'], 'methods': ['POST']}
                values.append(
                    self._prepare_endpoint_vals(
                        service, method_name, default_route, route_params
                    )
                )

        route_handler = self.env["endpoint.route.handler"]
        for vals in values:
            endpoint_handler = partial(
                RestController()._process_method, service._usage, method_name
            )
            new_route = route_handler.new(vals)
            new_route._register_controller(
                endpoint_handler=endpoint_handler, key=vals["name"]
            )

    def _prepare_endpoint_vals(self, service, method_name, route, routing_params):
        request_method = routing_params["methods"][0]
        name = (
            f"{self.tech_name}::{service._name}/{method_name}__{request_method.lower()}"
        )
        endpoint_vals = dict(
            name=name,
            request_method=request_method,
            route=route,
            route_group=self._route_group(),
            auth_type=self.auth_type,
        )
        return endpoint_vals

    def _route_group(self):
        return f"{self._name}:{self.tech_name}"

    def _get_services(self):
        return self.env["rest.service.registration"]._get_services(self._name)
