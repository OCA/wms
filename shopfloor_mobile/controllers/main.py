import os

from odoo import http


class ShopfloorMobileAppController(http.Controller):

    module_path = os.path.split(os.path.dirname(os.path.realpath(__file__)))[0]

    @http.route(
        [
            "/shopfloormobile/scanner/<path:path_fragment>",
            "/shopfloormobile/scanner",
            "/shopfloormobile/scanner/demo",
            "/shopfloormobile/scanner/demo/<path:path_fragment>",
        ],
        auth="public",
    )
    def load_app_and_assets(self, path_fragment=""):
        # TODO Should be authorized via api.key except for the login ?
        if path_fragment.endswith((".js.map", "scriptElement")):
            # `js.map` -> JS maps called by debugger
            # `scriptElement` -> file imported via JS but not loaded
            return http.request.not_found()
        if path_fragment.startswith("src/"):
            # Serving an asset
            payload = os.path.join(self.module_path, "static", "wms", path_fragment)
        else:
            # Serving the app
            payload = os.path.join(self.module_path, "static", "wms", "index.html")
        return http.send_file(payload)
