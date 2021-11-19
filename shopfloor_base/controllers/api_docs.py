# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.http import request, route

from odoo.addons.base_rest.controllers.api_docs import (
    ApiDocsController as BaseController,
)


class ApiDocsController(BaseController):
    @route(
        [
            "/shopfloor/api-docs/<tech_name(shopfloor.app):collection>",
            "/shopfloor/api-docs/<tech_name(shopfloor.app):collection>/index.html",
        ],
        methods=["GET"],
        type="http",
        auth="public",
    )
    def shopfloor_index(self, collection, **params):
        primary_name = params.get("urls.primaryName")
        swagger_settings = {
            "urls": self._get_shopfloor_api_urls(collection),
            "urls.primaryName": primary_name,
        }
        values = {"swagger_settings": swagger_settings}
        return request.render("base_rest.openapi", values)

    @route(
        [
            "/shopfloor/api-docs/"
            "<tech_name(shopfloor.app):collection>/<string:service_name>.json",
        ],
        auth="public",
    )
    def shopfloor_api(self, collection, service_name):
        services = collection._get_services()
        try:
            service = [x for x in services if x._usage == service_name][0]
        except IndexError:
            return request.not_found()
        collection._prepare_non_decorated_endpoints(service)
        service.work.collection = collection
        openapi_doc = service.to_openapi(default_auth=collection.auth_type)
        return self.make_json_response(openapi_doc)

    def _get_api_urls(self):
        api_urls = super()._get_api_urls()
        # Inject shopfloor docs into global docs from base_rest
        return api_urls + self._get_shopfloor_api_urls()

    def _get_shopfloor_api_urls(self, app=None):
        """Retrieve shopfloor related URLs for all apps or only given one."""
        api_urls = []
        base_url = request.httprequest.host_url.rstrip("/")
        env = request.env
        apps = env["shopfloor.app"].sudo().search([]) if not app else [app]
        for app in apps:
            base_docs_url = f"{base_url}/{app.api_docs_url.strip('/')}"
            for service in app._get_services():
                api_urls.append(
                    {
                        "name": f"[Shopfloor app] {app.name}: {service._usage}",
                        "url": f"{base_docs_url}/{service._usage}.json",
                    }
                )
        api_urls = sorted(api_urls, key=lambda k: k["name"])
        return api_urls
