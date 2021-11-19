# Copyright 2021 Camptocamp SA (http://www.camptocamp.com)
# @author Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
from odoo.http import request

from odoo.addons.base_rest.apispec.base_rest_service_apispec import (
    BaseRestServiceAPISpec,
)
from odoo.addons.base_rest.apispec.rest_method_security_plugin import (
    RestMethodSecurityPlugin,
)


class ShopfloorRestServiceAPISpec(BaseRestServiceAPISpec):
    """
    Describe APIspec for Shopfloor services.
    """

    def _get_servers(self):
        try:
            # Get always current base URL (supports localhost:8069 too!)
            base_url = request.httprequest.host_url
        except (RuntimeError, UnboundLocalError):
            # Gracefully fallback to settings (mostly for tests)
            # or in any other cases you call this method w/out a proper request.
            env = self._service.env
            base_url = env["ir.config_parameter"].sudo().get_param("web.base.url")
        return [
            {
                "url": "%s/%s/%s"
                % (
                    base_url.rstrip("/"),
                    self._service.collection.api_route.strip("/"),
                    self._service._usage,
                )
            }
        ]

    def _get_plugins(self):
        plugins = super()._get_plugins()
        for plugin in plugins:
            if isinstance(plugin, RestMethodSecurityPlugin):
                # Add `user_endpoint` to auth types
                plugin._supported_user_auths = ("user", "user_endpoint")
                break
        return plugins
