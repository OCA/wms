# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# @author Thierry Ducrest <thierry.ducrest@camptocamp.com>
# @author Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


import json
import logging
import os

from odoo import http
from odoo.tools import DotDict

from ..utils import RUNNING_ENV, get_version

_logger = logging.getLogger(__name__)


class ShopfloorMobileAppMixin(object):

    module_path = os.path.split(os.path.dirname(os.path.realpath(__file__)))[0]
    main_template = "shopfloor_mobile_base.shopfloor_app_main"

    def _load_app(self, shopfloor_app, demo=False, **kw):
        return http.request.render(
            self.main_template,
            self._get_main_template_values(shopfloor_app, demo=demo, **kw),
        )

    def _get_main_template_values(self, shopfloor_app, demo=False, **kw):
        # TODO: move this to shopfloor_app model and wrap everything
        # into `app_info` key. Then we simply dump to json here.
        app_info = self._make_app_info(shopfloor_app, demo=demo)
        return {
            "app_info": app_info,
            "get_version": get_version,
        }

    def _make_app_info(self, shopfloor_app, demo=False):
        base_url = shopfloor_app.api_route.rstrip("/") + "/"
        auth_type = shopfloor_app.auth_type
        profile_required = shopfloor_app.profile_required
        return DotDict(
            name=shopfloor_app.name,
            short_name=shopfloor_app.short_name,
            base_url=base_url,
            manifest_url=shopfloor_app.url + "/manifest.json",
            auth_type=auth_type,
            profile_required=profile_required,
            demo_mode=demo,
            version=shopfloor_app.app_version,
            running_env=self._get_running_env(),
        )

    def _get_running_env(self):
        return RUNNING_ENV

    def _make_icons(self, shopfloor_app, fname, rel, sizes, img_type, url_pattern=None):
        app_version = shopfloor_app.app_version
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
        all_icons.extend(self._make_icons(shopfloor_app, fname, rel, sizes, img_type))
        # android icons
        rel = "icon"
        sizes = ("48x48", "72x72", "96x96", "144x144", "192x192")
        fname = "android-icon"
        img_type = "image/png"
        all_icons.extend(self._make_icons(shopfloor_app, fname, rel, sizes, img_type))
        # favicons
        rel = "icon"
        sizes = ("16x16", "32x32", "96x96")
        fname = "favicon"
        img_type = "image/png"
        all_icons.extend(self._make_icons(shopfloor_app, fname, rel, sizes, img_type))
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
