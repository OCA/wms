from werkzeug.exceptions import BadRequest

from odoo.http import request

from odoo.addons.base_rest.controllers import main

MENU_ID_HEADER = "HTTP_SERVICE_CTX_MENU_ID"
# (name, model, dest_key)
MENU_HEADER_RULE = (MENU_ID_HEADER, "shopfloor.menu", "menu")

PROFILE_ID_HEADER = "HTTP_SERVICE_CTX_PROFILE_ID"
PROFILE_HEADER_RULE = (PROFILE_ID_HEADER, "shopfloor.profile", "profile")


class ShopfloorController(main.RestController):
    _root_path = "/shopfloor/"
    _collection_name = "shopfloor.service"
    _default_auth = "api_key"
    # TODO: this should come from registered services.
    # We would need to change how their ctx is initialized tho
    # because ATM the ctx is computed before lookup.
    _service_headers_rules = {
        # no special header required for config
        "app/user_config": (),
        "scan_anything/scan": (),
        # profile header is required to get menu items
        # fmt: off
        # NOTE: turn off formatting here is mandatory
        # otherwise black removes the space and flake8 w/ complain the comma
        # before parenthesis which is required to make this a tuple!
        "app/menu": (PROFILE_HEADER_RULE, ),
        # profile + menu is required to call processes
        "process": (PROFILE_HEADER_RULE, MENU_HEADER_RULE, ),
        # fmt: on
    }

    def _get_component_context(self):
        """
        This method adds the component context:
        * the shopfloor menu in ``self.work.menu`` from the service Components
        * the shopfloor profile in ``self.work.profile`` from the service
          Components
        """
        res = super(ShopfloorController, self)._get_component_context()
        res["menu"] = None
        res["profile"] = None
        res.update(self._get_process_context(request))
        return res

    # TODO: add tests
    def _get_process_context(self, request):
        ctx = {}
        env = request.env
        headers = request.httprequest.environ
        # '/shopfloor/app/user_config' -> app/config
        service_path = request.httprequest.path.split(self._root_path)[-1]

        # default to process rule
        default = self._service_headers_rules["process"]
        headers_map = self._service_headers_rules.get(service_path, default)
        for header_name, model, dest_key in headers_map:
            try:
                rec_id = int(headers.get(header_name))
            except (TypeError, ValueError):
                raise BadRequest("{} must be set with an integer".format(header_name))
            rec = env[model].browse(rec_id).exists()
            if not rec:
                raise BadRequest(
                    "Record {} with ID = {} not found".format(model, rec_id)
                )
            ctx[dest_key] = rec
        return ctx
