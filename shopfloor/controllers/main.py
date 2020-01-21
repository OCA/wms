from odoo.http import request

from odoo.addons.base_rest.controllers import main


class ShopfloorController(main.RestController):
    _root_path = "/shopfloor/"
    _collection_name = "shopfloor.service"
    _default_auth = "api_key"

    def _get_component_context(self):
        """
        This method adds the component context:
        * the process name
        * the process menu
        """
        res = super(ShopfloorController, self)._get_component_context()
        headers = request.httprequest.environ
        for k, v in headers.items():
            if k.startswith("HTTP_SERVICE_CTX_"):
                key_name = k[17:].lower()
                res[key_name] = v
        return res
