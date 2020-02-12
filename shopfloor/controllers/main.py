from werkzeug.exceptions import BadRequest

from odoo.http import request

from odoo.addons.base_rest.controllers import main


class ShopfloorController(main.RestController):
    _root_path = "/shopfloor/"
    _collection_name = "shopfloor.service"
    _default_auth = "api_key"
    _non_process_services = ("app", "menu", "profile")

    def _get_component_context(self):
        """
        This method adds the component context:
        * the shopfloor menu in ``self.work.menu`` from the service Components
        * the shopfloor profile in ``self.work.profile`` from the service
          Components
        """
        res = super(ShopfloorController, self)._get_component_context()
        headers = request.httprequest.environ

        res["menu"] = None
        res["profile"] = None
        if self._is_process_enpoint(request.httprequest.path):
            res.update(self._get_process_context(headers, request.env))
        return res

    def _is_process_enpoint(self, request_path):
        # '/shopfloor/app/user_config' -> app/config
        service_path = request_path.split(self._root_path)[-1]
        return not service_path.startswith(self._non_process_services)

    def _get_process_context(self, headers, env):
        ctx = {}
        try:
            menu_id = int(headers.get("HTTP_SERVICE_CTX_MENU_ID"))
        except (TypeError, ValueError):
            raise BadRequest("HTTP_SERVICE_CTX_MENU_ID must be set with an integer")
        ctx["menu"] = env["shopfloor.menu"].browse(menu_id)

        try:
            profile_id = int(headers.get("HTTP_SERVICE_CTX_PROFILE_ID"))
        except (TypeError, ValueError):
            raise BadRequest("HTTP_SERVICE_CTX_PROFILE_ID must be set with an integer")
        ctx["profile"] = env["shopfloor.profile"].browse(profile_id)
        return ctx
