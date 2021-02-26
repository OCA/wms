# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# Copyright 2020 Akretion (http://www.akretion.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from werkzeug.exceptions import BadRequest

from odoo import _, exceptions
from odoo.http import request
from odoo.osv import expression
from odoo.tools import DotDict

from odoo.addons.component.core import AbstractComponent

from ..actions.base_action import get_actions_for


class BaseShopfloorService(AbstractComponent):
    """Base class for REST services"""

    _inherit = "base.rest.service"
    _name = "base.shopfloor.service"
    _collection = "shopfloor.service"
    _expose_model = None

    def dispatch(self, method_name, *args, params=None):
        self._validate_headers_update_work_context(request, method_name)
        return super().dispatch(method_name, *args, params=params)

    def _actions_for(self, usage, **kw):
        return get_actions_for(self, usage, **kw)

    def _get(self, _id):
        domain = expression.normalize_domain(self._get_base_search_domain())
        domain = expression.AND([domain, [("id", "=", _id)]])
        record = self.env[self._expose_model].search(domain)
        if not record:
            raise exceptions.MissingError(
                _("The record %s %s does not exist") % (self._expose_model, _id)
            )
        else:
            return record

    def _get_base_search_domain(self):
        return []

    def _convert_one_record(self, record):
        """To implement in service Components"""
        return {}

    def _to_json(self, records):
        res = []
        for record in records:
            res.append(self._convert_one_record(record))
        return res

    def _response(
        self, base_response=None, data=None, next_state=None, message=None, popup=None
    ):
        """Base "envelope" for the responses

        All the keys are optional.

        :param base_response: optional dictionary of values to extend
        (typically already created by a call to _response())
        :param data: dictionary of values, when a next_state is provided,
        the data is enclosed in a key of the same name (to support polymorphism
        in the schema)
        :param next_state: string describing the next state that the client
        application must reach
        :param message: dictionary for the message to show in the client
        application (see ``_response_schema`` for the keys)
        :param popup: dictionary for a popup to show in the client application
        (see ``_response_schema`` for the keys). The popup is displayed before
        reaching the next state.
        """
        if base_response:
            response = base_response.copy()
        else:
            response = {}
        if next_state:
            # data for a state is always enclosed in a key with the name
            # of the state, so an endpoint can return to different states
            # that need different data: the schema can be different for
            # every state this way
            response.update(
                {
                    # ensure we have an empty dict when the state
                    # does not need any data, so the client does not need
                    # to check this
                    "data": {next_state: data or {}},
                    "next_state": next_state,
                }
            )

        elif data:
            response["data"] = data

        if message:
            response["message"] = message

        if popup:
            response["popup"] = popup

        return response

    _requires_header_menu = False
    _requires_header_profile = False

    def _get_openapi_default_parameters(self):
        defaults = super()._get_openapi_default_parameters()
        # Normal users can't read an API key, ignore it using sudo() only
        # because it's a demo key.
        demo_api_key = self.env.ref("shopfloor.api_key_demo", raise_if_not_found=False)
        if demo_api_key:
            demo_api_key = demo_api_key.sudo()

        service_params = [
            {
                "name": "API-KEY",
                "in": "header",
                "description": "API key for Authorization",
                "required": True,
                "schema": {"type": "string"},
                "style": "simple",
                "value": demo_api_key.key if demo_api_key else "",
            },
        ]
        if self._requires_header_menu:
            # Try to first the first menu that implements the current service.
            # Not all usages have a process, in that case, we'll set the first
            # menu found
            menu = self.env["shopfloor.menu"].search(
                [("scenario", "=", self._usage)], limit=1
            )
            if not menu:
                menu = self.env["shopfloor.menu"].search([], limit=1)
            service_params.append(
                {
                    "name": "SERVICE_CTX_MENU_ID",
                    "in": "header",
                    "description": "ID of the current menu",
                    "required": True,
                    "schema": {"type": "integer"},
                    "style": "simple",
                    "value": menu.id,
                }
            )
        if self._requires_header_profile:
            profile = self.env["shopfloor.profile"].search([], limit=1)
            service_params.append(
                {
                    "name": "SERVICE_CTX_PROFILE_ID",
                    "in": "header",
                    "description": "ID of the current profile",
                    "required": True,
                    "schema": {"type": "integer"},
                    "style": "simple",
                    "value": profile.id,
                }
            ),
        defaults.extend(service_params)
        return defaults

    @property
    def data(self):
        return self._actions_for("data")

    @property
    def data_detail(self):
        return self._actions_for("data_detail")

    @property
    def schema(self):
        return self._actions_for("schema")

    @property
    def schema_detail(self):
        return self._actions_for("schema_detail")

    @property
    def msg_store(self):
        return self._actions_for("message")

    # TODO: maybe to be proposed to base_rest
    # TODO: add tests
    def _validate_headers_update_work_context(self, request, method_name):
        """Validate request and update context per service.

        Our services may require extra headers.
        The service component is loaded after the ctx has been initialized
        hence we need an hook were we can validate by component/service
        if the request is compliant with what we need (eg: missing header)
        """
        if self.env.context.get("_service_skip_request_validation"):
            return
        extra_work_ctx = {}
        headers = request.httprequest.environ
        for rule, active in self._validation_rules:
            if callable(active):
                active = active(request, method_name)
            if not active:
                continue
            header_name, coerce_func, ctx_value_handler_name, mandatory = rule
            try:
                header_value = coerce_func(headers.get(header_name))
            except (TypeError, ValueError) as err:
                if not mandatory:
                    continue
                raise BadRequest(
                    "{} header validation error: {}".format(header_name, str(err))
                )
            ctx_value_handler = getattr(self, ctx_value_handler_name)
            dest_key, value = ctx_value_handler(header_value)
            if not value:
                raise BadRequest("{} header value lookup error".format(header_name))
            extra_work_ctx[dest_key] = value
        for k, v in extra_work_ctx.items():
            setattr(self.work, k, v)

    @property
    def _validation_rules(self):
        return (
            # rule to apply, active flag
            (self.MENU_ID_HEADER_RULE, self._requires_header_menu),
            (self.PROFILE_ID_HEADER_RULE, self._requires_header_profile),
        )

    MENU_ID_HEADER_RULE = (
        # header name, coerce func, ctx handler, mandatory
        "HTTP_SERVICE_CTX_MENU_ID",
        int,
        "_work_ctx_get_menu_id",
        True,
    )
    PROFILE_ID_HEADER_RULE = (
        # header name, coerce func, ctx value handler, mandatory
        "HTTP_SERVICE_CTX_PROFILE_ID",
        int,
        "_work_ctx_get_profile_id",
        True,
    )

    def _work_ctx_get_menu_id(self, rec_id):
        return "menu", self.env["shopfloor.menu"].browse(rec_id).exists()

    def _work_ctx_get_profile_id(self, rec_id):
        return "profile", self.env["shopfloor.profile"].browse(rec_id).exists()

    _options = {}

    @property
    def options(self):
        """Compute options for current service.

        If the service has a menu, options coming from the menu are injected.
        """
        if self._options:
            return self._options

        options = {}
        if self._requires_header_menu and getattr(self.work, "menu", None):
            options = self.work.menu.scenario_id.options or {}
        options.update(getattr(self.work, "options", {}))
        self._options = DotDict(options)
        return self._options


class BaseShopfloorProcess(AbstractComponent):
    """Base class for process rest service"""

    _inherit = "base.shopfloor.service"
    _name = "base.shopfloor.process"

    _requires_header_menu = True
    _requires_header_profile = True
