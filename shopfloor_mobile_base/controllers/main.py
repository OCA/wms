# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# @author Thierry Ducrest <thierry.ducrest@camptocamp.com>
# @author Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


import json
import os

from odoo import http
from odoo.modules.module import load_information_from_description_file

APP_VERSIONS = {}


class ShopfloorMobileAppMixin(object):

    module_path = os.path.split(os.path.dirname(os.path.realpath(__file__)))[0]
    main_template = "shopfloor_mobile_base.shopfloor_app_main"

    def _load_app(self, demo=False, **kw):
        return http.request.render(
            self.main_template, self._get_main_template_values(demo=demo, **kw)
        )

    def _get_main_template_values(self, demo=False, **kw):
        return dict(
            app_version=self._get_app_version(),
            get_version=self._get_version,
            demo_mode=demo,
            **kw
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
        return self._get_version("shopfloor_mobile_base", module_path=self.module_path)

    def _serve_assets(self, path_fragment="", **kw):
        # TODO Should be authorized via api.key except for the login ?
        if path_fragment.endswith((".map", "scriptElement")):
            # `.map` -> .map maps called by debugger
            # `scriptElement` -> file imported via JS but not loaded
            return http.request.not_found()
        if path_fragment.startswith("src/"):
            # Serving an asset
            payload = self._make_asset_path(path_fragment)
            if os.path.exists(payload):
                return http.send_file(payload)
        return http.request.not_found()

    def _make_asset_path(self, path_fragment):
        return os.path.join(self.module_path, "static", "wms", path_fragment)

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

    def _get_app_icons(self):
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

    def _get_manifest(self):
        return {
            "name": "Shopfloor WMS app",
            "short_name": "Shopfloor",
            "start_url": "/shopfloor_mobile/app/#",
            "display": "fullscreen",
            "icons": self._get_app_icons(),
        }


class ShopfloorMobileAppController(http.Controller, ShopfloorMobileAppMixin):
    @http.route(
        ["/shopfloor_mobile/app", "/shopfloor_mobile/app/<string:demo>"], auth="public",
    )
    def load_app(self, demo=False, **kw):
        return self._load_app(demo=True if demo else False, **kw)

    @http.route(
        ["/shopfloormobile/scanner"], auth="public",
    )
    def load_app_backward(self, demo=False):
        # Backward compat redirect (url changed from /scanner to /app)
        return http.redirect_with_hash("/shopfloor_mobile/app", code=301)

    # TODO: do we really need this?
    @http.route(
        ["/shopfloor_mobile/assets/<path:path_fragment>"], auth="public",
    )
    def load_assets(self, path_fragment="", **kw):
        return self._serve_assets(path_fragment=path_fragment, **kw)

    @http.route("/shopfloor_mobile/manifest.json", auth="public")
    def manifest(self):
        manifest = self._get_manifest()
        headers = {}
        headers["Content-Type"] = "application/json"
        return http.request.make_response(json.dumps(manifest), headers=headers)
