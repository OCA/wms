from odoo.addons.base_rest.controllers import main
from odoo.exceptions import MissingError
from odoo.http import request


class ShopfloorController(main.RestController):
    _root_path = "/shopfloor/"
    _collection_name = "shopfloor.services"
    _default_auth = "api_key"

    @classmethod
    def _get_process_from_headers(cls, headers):
        process_name = headers.get("HTTP_SERVICE_CTX_PROCESS_NAME")
        return process_name

    @classmethod
    def _get_process_menu_from_headers(cls, headers):
        process_menu = headers.get("HTTP_SERVICE_CTX_PROCESS_MENU")
        return process_menu

    def _get_component_context(self):
        """
        This method adds the component context:
        * the process name
        * the process menu
        """
        res = super(ShopfloorController, self)._get_component_context()
        headers = request.httprequest.environ
        res["process_name"] = self._get_process_from_headers(headers)
        res["process_menu"] = self._get_process_menu_from_headers(headers)
        return res
