# Copyright 2021 Camptocamp SA (http://www.camptocamp.com)
# @author Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import logging

from odoo import api, fields, models, tools
from odoo.tools import DotDict

from odoo.addons.base_rest.tools import _inspect_methods
from odoo.addons.component.core import _component_databases

from ..utils import APP_VERSION, RUNNING_ENV

_logger = logging.getLogger(__file__)


class ShopfloorApp(models.Model):
    """Backend for a Shopfloor app."""

    _name = "shopfloor.app"
    _inherit = ["collection.base", "endpoint.route.sync.mixin"]
    _description = "A Shopfloor application"

    name = fields.Char(required=True, translate=True)
    short_name = fields.Char(
        required=True, translate=True, help="Needed for app manifest"
    )
    # Unique name
    tech_name = fields.Char(required=True, index=True)
    active = fields.Boolean(default=True)
    category = fields.Selection(selection=[("", "None")])
    api_route = fields.Char(
        compute="_compute_api_route",
        compute_sudo=True,
        help="Base route for endpoints attached to this app, public version.",
    )
    api_route = fields.Char(
        compute="_compute_api_route",
        compute_sudo=True,
        help="""
        Base route for endpoints attached to this app,
        internal controller-ready version.
        """,
    )
    url = fields.Char(compute="_compute_url", help="Public URL to use the app.")
    api_docs_url = fields.Char(compute="_compute_url", help="Public URL for api docs.")
    auth_type = fields.Selection(
        selection="_selection_auth_type", default="user_endpoint"
    )
    registered_routes = fields.Text(
        compute="_compute_registered_routes",
        compute_sudo=True,
        help="Technical field to allow developers to check registered routes on the form",
        groups="base.group_no_one",
    )
    profile_ids = fields.Many2many(
        comodel_name="shopfloor.profile",
        string="Profiles",
        help="Profiles used by this app. "
        "This will determine menu items too."
        "However this field is not required "
        "in case you don't need profiles and menu items from the backend.",
    )
    profile_required = fields.Boolean(compute="_compute_profile_required", store=True)
    app_version = fields.Char(compute="_compute_app_version")
    lang_id = fields.Many2one(
        "res.lang",
        string="Default language",
        help="If set, the app will be first loaded with this lang.",
    )
    lang_ids = fields.Many2many("res.lang", string="Available languages")

    _sql_constraints = [("tech_name", "unique(tech_name)", "tech_name must be unique")]

    _api_route_path = "/shopfloor/api/"

    @api.depends("tech_name")
    def _compute_api_route(self):
        for rec in self:
            rec.api_route = rec._api_route_path + rec.tech_name

    _base_url_path = "/shopfloor/app/"
    _base_api_docs_url_path = "/shopfloor/api-docs/"

    @api.depends("tech_name")
    def _compute_url(self):
        for rec in self:
            full_url = rec._base_url_path + rec.tech_name
            rec.url = full_url.rstrip("/") + "/"
            rec.api_docs_url = rec._base_api_docs_url_path + rec.tech_name

    @api.depends("tech_name")
    def _compute_registered_routes(self):
        for rec in self:
            routes = sorted(rec._registered_routes(), key=lambda x: x.route)
            vals = []
            for endpoint_rule in routes:
                vals.append(
                    f"{endpoint_rule.route} ({', '.join(endpoint_rule.routing['methods'])})"
                )
            rec.registered_routes = "\n".join(vals)

    @api.depends("profile_ids")
    def _compute_profile_required(self):
        for rec in self:
            rec.profile_required = bool(rec.profile_ids)

    def _compute_app_version(self):
        # Override this to choose your own versioning policy
        for rec in self:
            rec.app_version = APP_VERSION

    def _selection_auth_type(self):
        return self.env["endpoint.route.handler"]._selection_auth_type()

    def api_url_for_service(self, service_name, endpoint=None):
        """Handy method to generate services' API URLs for current app."""
        return f"{self.api_route}/{service_name}/{endpoint or ''}".rstrip("/")

    def action_open_app(self):
        return {
            "type": "ir.actions.act_url",
            "name": self.name,
            "url": self.url,
            "target": "new",
        }

    def action_open_app_docs(self):
        return {
            "type": "ir.actions.act_url",
            "name": self.name,
            "url": self.api_docs_url,
            "target": "new",
        }

    def action_view_menu_items(self):
        xid = "shopfloor_base.action_shopfloor_menu"
        action = self.env["ir.actions.act_window"]._for_xml_id(xid)
        action["domain"] = [
            "|",
            ("id", "in", self.profile_ids.menu_ids.ids),
            ("profile_id", "=", False),
        ]
        return action

    def _routing_impacting_fields(self):
        return ("tech_name", "auth_type")

    def _prepare_endpoint_rules(self, options=None):
        # `endpoint.route.sync.mixin` api
        services = self._get_services()
        routes = []
        for service in services:
            self._prepare_non_decorated_endpoints(service)
            routes.extend(self._generate_endpoints(service))

        rules = [
            rec._make_controller_rule(key=rec.name, options=options)
            for rec, options in routes
        ]
        return rules

    def _registered_endpoint_rule_keys(self):
        # `endpoint.route.sync.mixin` api
        return [x[0] for x in self._registered_routes()]

    def _register_hook(self):
        super()._register_hook()
        if not tools.sql.column_exists(self.env.cr, self._table, "registry_sync"):
            # `registry_sync` has been introduced recently.
            # If an env is loaded before the column gets created this can be broken.
            return True
        self._boot_base_rest_endpoints()

    def _boot_base_rest_endpoints(self):
        """Satisfy `base_rest` requirements for REST requests.

        1. register root paths
        2. decorate non decorated endpoints

        Note that at runtime this is done by
        `_register_controllers` and `_prepare_endpoint_rules`.

        TODO: trash for v16 if using `fastapi`.
        """
        domain = [("active", "=", True), ("registry_sync", "=", True)]
        self.search(domain)._register_base_rest_routes()
        services = self._get_services()
        for service in services:
            self._prepare_non_decorated_endpoints(service)

    def _register_controllers(self, init=False, options=None):
        super()._register_controllers(init=init, options=options)
        if not self:
            return
        self._register_base_rest_routes()

    def _register_base_rest_routes(self):
        # base_rest patches odoo http request to handle json request
        # using a special registry for rest routes
        for rec in self:
            self.env["rest.service.registration"]._register_rest_route(rec.api_route)

    def _registered_routes(self):
        registry = self.env["endpoint.route.handler"]._endpoint_registry
        return registry.get_rules_by_group(self._route_group())

    @api.model
    def _prepare_non_decorated_endpoints(self, service):
        # Autogenerate routing info where missing
        self.env["rest.service.registration"]._prepare_non_decorated_endpoints(service)

    def _generate_endpoints(self, service):
        res = []
        for rec in self:
            values = rec._generate_endpoints_values(service)
            for vals in values:
                route, options = rec._generate_endpoints_route(service, vals)
                res.append((route, options))
        return res

    def _generate_endpoints_values(self, service):
        values = []
        root_path = self.api_route.rstrip("/") + "/" + service._usage
        for name, method in _inspect_methods(service.__class__):
            if not hasattr(method, "routing"):
                continue
            routing = method.routing
            for routes, http_method in routing["routes"]:
                # TODO: why on base_rest we have this instead of pure method name?
                # method_name = "{}_{}".format(http_method.lower(), name)
                method_name = name
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
        return values

    def _generate_endpoints_route(self, service, vals):
        method_name = vals.pop("_method_name")
        route_handler = self.env["endpoint.route.handler.tool"]
        new_route = route_handler.new(vals)
        new_route._refresh_endpoint_data()
        options = {
            "handler": {
                "klass_dotted_path": (
                    "odoo.addons.shopfloor_base.controllers.main.ShopfloorController"
                ),
                "method_name": "_process_endpoint",
                "default_pargs": (self.id, service._usage, method_name),
            }
        }
        return new_route, options

    def _prepare_endpoint_vals(self, service, method_name, route, routing_params):
        request_method = routing_params["methods"][0]
        name = f"app#{self.id}::{service._name}/{method_name}__{request_method.lower()}"
        endpoint_vals = dict(
            name=name,
            request_method=request_method,
            route=route,
            route_group=self._route_group(),
            auth_type=self.auth_type,
            _method_name=method_name,
        )
        return endpoint_vals

    def _route_group(self):
        return f"{self._name}:{self.tech_name}"

    def _is_component_registry_ready(self):
        comp_registry = _component_databases.get(self.env.cr.dbname)
        return comp_registry and comp_registry.ready

    def _get_services(self):
        forced_services = self.env.context.get("sf_service_components")
        if forced_services:
            _logger.debug(
                "_get_services forced services: %s",
                ", ".join([x._usage for x in forced_services]),
            )
            return forced_services
        if not self._is_component_registry_ready():
            # No service is available before the registry has been loaded.
            # This is a very special case, when the odoo registry is being
            # built, it calls odoo.modules.loading.load_modules().
            return []
        return self.env["rest.service.registration"]._get_services(self._name)

    def _name_with_env(self):
        name = self.name
        if RUNNING_ENV and RUNNING_ENV != "prod":
            name += f" ({RUNNING_ENV})"
        return name

    def _make_app_info(self, demo=False):
        base_url = self.api_route.rstrip("/") + "/"
        return DotDict(
            name=self._name_with_env(),
            short_name=self.short_name,
            base_url=base_url,
            url=self.url,
            manifest_url=self.url + "manifest.json",
            auth_type=self.auth_type,
            profile_required=self.profile_required,
            demo_mode=demo,
            version=self.app_version,
            running_env=RUNNING_ENV,
            lang=self._app_info_lang(),
        )

    def _app_info_lang(self):
        enabled = []
        conv = self._app_convert_lang_code
        if self.lang_ids:
            enabled = [conv(x.code) for x in self.lang_ids]
        return dict(
            default=conv(self.lang_id.code) if self.lang_id else False,
            enabled=enabled,
        )

    def _app_convert_lang_code(self, code):
        # TODO: we should probably let the front decide the format
        return code.replace("_", "-")

    def _make_app_manifest(self, icons=None, **kw):
        param = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("web.base.url", "")
            .rstrip("/")
        )
        manifest = {
            "name": self._name_with_env(),
            "short_name": self.short_name,
            "start_url": param + self.url,
            "scope": param + self.url,
            "id": self.url,
            "display": "fullscreen",
            "icons": icons or [],
        }
        manifest.update(kw)
        return manifest

    @api.onchange("lang_id")
    def _onchange_lang_id(self):
        if self.env.context.get("from_onchange__lang_ids"):
            return
        if self.lang_id and self.lang_id not in self.lang_ids:
            self.with_context(from_onchange__lang_id=1).lang_ids += self.lang_id

    @api.onchange("lang_ids")
    def _onchange_lang_ids(self):
        if self.env.context.get("from_onchange__lang_id"):
            return
        if self.lang_ids and self.lang_id and self.lang_id not in self.lang_ids:
            self.with_context(from_onchange__lang_ids=1).lang_id = False
