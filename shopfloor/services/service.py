from odoo import _, exceptions, registry
from odoo.exceptions import MissingError
from odoo.http import request
from odoo.osv import expression

from odoo.addons.base_rest.controllers.main import _PseudoCollection
from odoo.addons.component.core import AbstractComponent, WorkContext


def to_float(val):
    if isinstance(val, float):
        return val
    if val:
        return float(val)
    return None


class BaseShopfloorService(AbstractComponent):
    """Base class for REST services"""

    _inherit = "base.rest.service"
    _name = "base.shopfloor.service"
    _collection = "shopfloor.service"
    _actions_collection_name = "shopfloor.action"
    _expose_model = None

    def dispatch(self, method_name, _id=None, params=None):
        try:
            result = super().dispatch(method_name, _id=_id, params=params)
        except Exception as err:
            self.env.cr.rollback()
            with registry(self.env.cr.dbname).cursor() as cr:
                env = self.env(cr=cr)
                self._log_call_in_db(env, _id, params, error=err)
            raise
        self._log_call_in_db(self.env, _id, params, result=result)
        return result

    @property
    def _log_call_header_strip(self):
        return ("Cookie", "Api-Key")

    def _log_call_in_db_values(self, _id, params, result=None, error=None):
        if not request:
            # In tests, we have no http request
            return
        httprequest = request.httprequest
        headers = dict(httprequest.headers)
        for header_key in self._log_call_header_strip:
            if header_key in headers:
                headers[header_key] = "<redacted>"
        if _id:
            params = dict(params, _id=_id)
        return {
            "request_url": httprequest.url,
            "request_method": httprequest.method,
            "params": params,
            "headers": headers,
            "result": result,
            "error": error,
            "state": "success" if result else "failed",
        }

    def _log_call_in_db(self, env, _id, params, result=None, error=None):
        if not env["shopfloor.log"].logging_active():
            return
        values = self._log_call_in_db_values(_id, params, result=result, error=error)
        if not values:
            return
        env["shopfloor.log"].sudo().create(values)

    def _get(self, _id):
        domain = expression.normalize_domain(self._get_base_search_domain())
        domain = expression.AND([domain, [("id", "=", _id)]])
        record = self.env[self._expose_model].search(domain)
        if not record:
            raise MissingError(
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

    def _get_input_validator(self, method_name):
        # override the method to get the validator in a component
        # instead of a method, to keep things apart
        validator_component = self.component(usage="%s.validator" % self._usage)
        return validator_component._get_validator(method_name)

    def _get_output_validator(self, method_name):
        # override the method to get the validator in a component
        # instead of a method, to keep things apart
        validator_component = self.component(
            usage="%s.validator.response" % self._usage
        )
        return validator_component._get_validator(method_name)

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
        demo_api_key = self.env.ref(
            "shopfloor.api_key_demo", raise_if_not_found=False
        ).sudo()
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
    def actions_collection(self):
        return _PseudoCollection(self._actions_collection_name, self.env)

    def actions_for(self, usage):
        """Return an Action Component for a usage

        Action Components are the components supporting the business logic of
        the processes, so we can limit the code in Services to the minimum and
        share methods.
        """
        # propagate custom arguments (such as menu ID/profile ID)
        kwargs = {
            attr_name: getattr(self.work, attr_name)
            for attr_name in self.work._propagate_kwargs
            if attr_name not in ("collection", "components_registry")
        }
        work = WorkContext(collection=self.actions_collection, **kwargs)
        return work.component(usage=usage)

    def _is_public_api_method(self, method_name):
        # do not "hide" the "actions_for" method as internal since, we'll use
        # it in components, so exclude it from the rest API
        if method_name == "actions_for":
            return False
        return super()._is_public_api_method(method_name)


class BaseShopfloorProcess(AbstractComponent):
    """Base class for process rest service"""

    _inherit = "base.shopfloor.service"
    _name = "base.shopfloor.process"

    _requires_header_menu = True
    _requires_header_profile = True

    @property
    def picking_types(self):
        """Return picking types for the menu and profile"""
        # TODO make this a lazy property or computed field avoid running the
        # filter every time?
        picking_types = self.work.menu.picking_type_ids.filtered(
            lambda pt: not pt.warehouse_id
            or pt.warehouse_id == self.work.profile.warehouse_id
        )
        if not picking_types:
            raise exceptions.UserError(
                _("No operation types configured on menu {} for warehouse {}.").format(
                    self.work.menu.name, self.work.profile.warehouse_id.display_name
                )
            )
        return picking_types
