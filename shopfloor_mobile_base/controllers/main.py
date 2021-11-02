# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# @author Thierry Ducrest <thierry.ducrest@camptocamp.com>
# @author Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


import json
import logging
import os

from odoo import http
from odoo.modules.module import load_information_from_description_file
from odoo.tools.config import config as odoo_config

_logger = logging.getLogger(__name__)


APP_VERSIONS = {}


def _get_running_env():
    """Retrieve current system environment.

    Expected key `RUNNING_ENV` is compliant w/ `server_environment` naming
    but is not depending on it.

    Additionally, as specific key for Shopfloor is supported.

    You don't need `server_environment` module to have this feature.
    """
    for key in ("SHOPFLOOR_RUNNING_ENV", "RUNNING_ENV"):
        if os.getenv(key):
            return os.getenv(key)
        if odoo_config.options.get(key.lower()):
            return odoo_config.get(key.lower())
    return "prod"


RUNNING_ENV = _get_running_env()


class ShopfloorMobileAppMixin(object):

    module_path = os.path.split(os.path.dirname(os.path.realpath(__file__)))[0]
    main_template = "shopfloor_mobile_base.shopfloor_app_main"

    def _load_app(self, shopfloor_app=None, demo=False, **kw):
        return http.request.render(
            self.main_template,
            self._get_main_template_values(
                shopfloor_app=shopfloor_app, demo=demo, **kw
            ),
        )

    def _get_main_template_values(self, shopfloor_app=None, demo=False, **kw):
        # TODO: move this to shopfloor_app model and wrap everything
        # into `app_info` key. Then we simply dump to json here.
        app_info = self._make_app_info(shopfloor_app=shopfloor_app, demo=demo)
        return {
            "app_info": app_info,
            "get_version": self._get_version,
        }

    def _make_app_info(self, shopfloor_app=None, demo=False):
        base_url = (
            shopfloor_app.api_route_public + "/" if shopfloor_app else "/shopfloor/"
        )
        # TODO: shopfloor_app should be mandatory at this stage.
        auth_type = shopfloor_app.auth_type
        return dict(
            base_url=base_url,
            auth_type=auth_type,
            demo_mode=demo,
            version=self._get_app_version(),
            running_env=self._get_running_env(),
        )

    def _get_version(self, module_name, module_path=None):
        """Return module version straight from manifest."""
        global APP_VERSIONS
        if APP_VERSIONS.get(module_name):
            return APP_VERSIONS[module_name]
        try:
            info = load_information_from_description_file(
                module_name, mod_path=module_path
            )
            APP_VERSIONS[module_name] = info["version"]
            return APP_VERSIONS[module_name]
        except Exception:
            return "dev"

    def _get_app_version(self):
        return self._get_version("shopfloor_mobile_base")

    def _get_running_env(self):
        return RUNNING_ENV

    def _make_icons(self, fname, rel, sizes, img_type, url_pattern=None):
        app_version = self._get_app_version()
        all_icons = []
        url_pattern = url_pattern or (
            "/shopfloor_mobile_base/static/wms/src/assets/icons/"
            "{fname}-{size}.png?v={app_version}"
        )
        for size in sizes:
            all_icons.append(
                {
                    "rel": rel,
                    "src": url_pattern.format(
                        app_version=app_version, fname=fname, size=size
                    ),
                    "sizes": size,
                    "type": img_type,
                }
            )
        return all_icons

    def _get_app_icons(self, shopfloor_app):
        all_icons = []
        # apple icons
        rel = "apple-touch-icon"
        sizes = (
            "57x57",
            "60x60",
            "72x72",
            "76x76",
            "114x114",
            "120x120",
            "144x144",
            "152x152",
            "180x180",
        )
        fname = "apple-icon"
        img_type = "image/png"
        all_icons.extend(self._make_icons(fname, rel, sizes, img_type))
        # android icons
        rel = "icon"
        sizes = ("48x48", "72x72", "96x96", "144x144", "192x192")
        fname = "android-icon"
        img_type = "image/png"
        all_icons.extend(self._make_icons(fname, rel, sizes, img_type))
        # favicons
        rel = "icon"
        sizes = ("16x16", "32x32", "96x96")
        fname = "favicon"
        img_type = "image/png"
        all_icons.extend(self._make_icons(fname, rel, sizes, img_type))
        return all_icons

    def _get_manifest(self, shopfloor_app):
        return {
            "name": shopfloor_app.name,
            "short_name": shopfloor_app.short_name,
            "start_url": shopfloor_app.url + "#",
            "display": "fullscreen",
            "icons": self._get_app_icons(shopfloor_app),
        }


class ShopfloorMobileAppController(http.Controller, ShopfloorMobileAppMixin):
    @http.route(
        [
            "/shopfloor/app/<tech_name(shopfloor.app):shopfloor_app>",
            "/shopfloor/app/<tech_name(shopfloor.app):shopfloor_app>/<string:demo>",
        ],
        auth="public",
    )
    def load_app(self, shopfloor_app, demo=False, **kw):
        return self._load_app(shopfloor_app, demo=True if demo else False, **kw)

    @http.route(
        ["/shopfloor_mobile/app"],
        auth="public",
    )
    def load_app_backward(self, demo=False):
        # Backward compat redirect to the 1st matching app if any.
        model = http.request.env["shopfloor.app"]
        # TODO: create a default app and redirect to it automatically.
        # Then make `shopfloor_app` required at every step in `_load_app`.
        app = model.search([], limit=1)
        if app:
            return http.redirect_with_hash(app.url, code=301)
        _logger.error("No matching app")
        return http.request.not_found()

    @http.route(
        [
            "/shopfloor/app/<tech_name(shopfloor.app):shopfloor_app>/manifest.json",
        ],
        auth="public",
    )
    def manifest(self, shopfloor_app):
        manifest = self._get_manifest(shopfloor_app)
        headers = {}
        headers["Content-Type"] = "application/json"
        return http.request.make_response(json.dumps(manifest), headers=headers)
