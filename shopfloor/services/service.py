from odoo import _
from odoo.exceptions import MissingError
from odoo.osv import expression

from odoo.addons.base_rest.controllers.main import _PseudoCollection
from odoo.addons.component.core import AbstractComponent, WorkContext


class BaseShopfloorService(AbstractComponent):
    """Base class for REST services"""

    _inherit = "base.rest.service"
    _name = "base.shopfloor.service"
    _collection = "shopfloor.service"
    _actions_collection_name = "shopfloor.action"
    _expose_model = None

    @property
    def picking_types(self):
        """
        Get the current picking type based on the menu and the warehouse of the profile.
        """
        return self.work.menu.process_id.picking_type_ids.filtered(
            lambda p: p.warehouse_id == self.work.profile.warehouse_id
        )

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

    def _response(self, data=None, state=None, message=None):
        """Base "envelope" for the responses

        All the keys are optional.

        :param data: dictionary of values
        :param state: string describing the next state that the client
        application must reach
        :param message: dictionary for the message to show in the client
        application (see ``_response_schema`` for the keys)
        """
        response = {}
        if data:
            response["data"] = data
        if state:
            response["state"] = state
        if message:
            response["message"] = message
        return response

    def _response_schema(self, data_schema=None):
        """Schema for the return validator

        Must be used for the schema of all responses.
        The "data" part can be customized and is optional,
        it must be a dictionary.
        """
        if not data_schema:
            data_schema = {}
        return {
            "data": {"type": "dict", "required": False, "schema": data_schema},
            "state": {"type": "string", "required": False},
            "message": {
                "type": "dict",
                "required": False,
                "schema": {
                    "message_type": {
                        "type": "string",
                        "required": True,
                        "allowed": ["info", "warning", "error"],
                    },
                    "message": {"type": "string", "required": True},
                },
            },
        }

    def _get_openapi_default_parameters(self):
        defaults = super()._get_openapi_default_parameters()
        demo_api_key = self.env.ref(
            "shopfloor.api_key_demo", raise_if_not_found=False
        ).key
        defaults.extend(
            [
                {
                    "name": "API-KEY",
                    "in": "header",
                    "description": "API key for Authorization",
                    "required": True,
                    "schema": {"type": "string"},
                    "style": "simple",
                    "value": demo_api_key,
                },
                {
                    "name": "SERVICE_CTX_MENU_ID",
                    "in": "header",
                    "description": "ID of the current menu",
                    "required": True,
                    "schema": {"type": "integer"},
                    "style": "simple",
                    "value": "1",
                },
                {
                    "name": "SERVICE_CTX_PROFILE_ID",
                    "in": "header",
                    "description": "ID of the current profile",
                    "required": True,
                    "schema": {"type": "integer"},
                    "style": "simple",
                    "value": "1",
                },
            ]
        )
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
