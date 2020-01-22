from werkzeug.exceptions import BadRequest

from odoo.http import request

from odoo.addons.base_rest.controllers import main


class ShopfloorController(main.RestController):
    _root_path = "/shopfloor/"
    _collection_name = "shopfloor.service"
    _default_auth = "api_key"

    def _get_component_context(self):
        """
        This method adds the component context:
        * the shopfloor menu in ``self.work.menu`` from the service Components
        * the shopfloor profile in ``self.work.profile`` from the service
          Components
        """
        res = super(ShopfloorController, self)._get_component_context()
        headers = request.httprequest.environ
        try:
            menu_id = int(headers.get("HTTP_SERVICE_CTX_MENU_ID"))
        except (TypeError, ValueError):
            raise BadRequest("HTTP_SERVICE_CTX_MENU_ID must be set with an integer")
        res["menu"] = request.env["shopfloor.menu"].browse(menu_id)

        try:
            profile_id = int(headers.get("HTTP_SERVICE_CTX_PROFILE_ID"))
        except (TypeError, ValueError):
            raise BadRequest("HTTP_SERVICE_CTX_PROFILE_ID must be set with an integer")
        res["profile"] = request.env["shopfloor.profile"].browse(profile_id)

        return res
