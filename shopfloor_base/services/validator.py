# Copyright 2020-2021 Camptocamp SA (http://www.camptocamp.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
import logging

from odoo.addons.component.core import AbstractComponent, Component
from odoo.addons.component.exception import NoComponentError

from ..actions.base_action import get_actions_for

_logger = logging.getLogger(__name__)


class ShopfloorRestCerberusValidator(Component):
    """Customize the handling of validators

    In the initial implementation of rest_api, the schema validators
    had to be returned by methods in the same service as the method, named
    after the endpoint's method with a prefix: "_validator_<method>" or
    "_validator_return_<method>".

    As we have a lot of endpoints methods in some services, we extracted
    the validator methods in dedicated components with
    "base.shopfloor.validator" and "base.shopfloor.validator.response" usages,
    and methods of the same name as the endpoint's method.

    With the new API, endpoints are decorated with "@restapi.method" and the
    validator is defined there. Example:

        @restapi.method(
            [(["/<int:id>/get", "/<int:id>"], "GET")],
            input_param=restapi.CerberusValidator("_get_partner_input_schema"),
            output_param=restapi.CerberusValidator("_get_partner_output_schema"),
            auth="public",
        )

    The schema is get by calling the method "_get..." on the service.

    For backward compatilibity, base_rest patches the methods not decorated
    and sets the "input_param" and "output_param" to call the
    "_validator_<method>" or "_validator_return_<method>":

    https://github.com/OCA/rest-framework/blob/abd74cd7241d3b93054825cc3e41cb7b693c9000/base_rest/models/rest_service_registration.py#L240-L250  # noqa

    The following change in base_rest allows to customize the way the validator
    handler is get: https://github.com/OCA/rest-framework/pull/99

    This is what is used here to delegate to our ".validator" and
    ".validator.response" components.
    """

    _name = "shopfloor.rest.cerberus.validator"
    _inherit = "base.rest.cerberus.validator"
    _usage = "cerberus.validator"
    _collection = "shopfloor.app"
    _is_rest_service_component = False

    def _get_validator_component(self, service, method_name, direction):
        assert direction in ("input", "output")
        if direction == "input":
            suffix = "validator"
            method_name = method_name.replace("_validator_", "")
        else:
            suffix = "validator.response"
            method_name = method_name.replace("_validator_return_", "")
        validator_component = self.component(
            usage="{}.{}".format(service._usage, suffix)
        )
        return validator_component, method_name

    def get_validator_handler(self, service, method_name, direction):
        """Get the validator handler for a method

        By default, it returns the method on the current service instance. It
        can be customized to delegate the validators to another component.
        """
        try:
            validator_component, method_name = self._get_validator_component(
                service, method_name, direction
            )
        except NoComponentError:
            _logger.warning("no component found for %s method %s", service, method_name)
            return None

        try:
            return getattr(validator_component, method_name)
        except AttributeError:
            _logger.warning(
                "no validator method found for %s method %s", service, method_name
            )
            return None

    def has_validator_handler(self, service, method_name, direction):
        """Return if the service has a validator handler for a method

        By default, it returns True if the the method exists on the service. It
        can be customized to delegate the validators to another component.
        """
        try:
            validator_component, method_name = self._get_validator_component(
                service, method_name, direction
            )
        except NoComponentError:
            return False
        return hasattr(validator_component, method_name)


class BaseShopfloorValidator(AbstractComponent):
    """Base class for Validators"""

    _inherit = "base.rest.service"
    _name = "base.shopfloor.validator"
    _collection = "shopfloor.app"
    _is_rest_service_component = False


class BaseShopfloorValidatorResponse(AbstractComponent):
    """Base class for Validator for Responses

    When an endpoint returns data for a state, the data is enclosed
    in a key with the same name as the state, this is in order to support
    polymorphism in schemas (an endpoint being able to return different data
    depending on the next state).

    General idea of a schema for a method that changes state (data may vary,
    in this example, next_state will be one of "confirm_start", "start",
    "scan_location"):

        {
          message {
            message_type* string
            message*      string
          }
          next_state      string
          data {
            confirm_start {...}
            start {...}
            scan_location {...}
          }
        }

    General idea of a schema for a generic method (data may vary):

        {
          message {
            message_type* string
            message*      string
          }
          data {
            size*         integer
            records*      integer
          }
        }

    """

    _inherit = "base.rest.service"
    _name = "base.shopfloor.validator.response"
    _collection = "shopfloor.app"
    _is_rest_service_component = False

    # Initial state of a workflow
    _start_state = "start"

    def _states(self):
        """List of possible next states

        With the schema of the data send to the client to transition
        to the next state.
        """
        return {}

    def _actions_for(self, usage, **kw):
        return get_actions_for(self, usage, **kw)

    @property
    def schemas(self):
        return self._actions_for("schema")

    @property
    def schemas_detail(self):
        return self._actions_for("schema_detail")

    def _response_schema(self, data_schema=None, next_states=None):
        """Schema for the return validator

        Must be used for the schema of all responses.
        The "data" part can be customized and is optional,
        it must be a dictionary.

        next_states is a list of allowed states to which the client
        can transition. The schema of the data needed for every state
        of the list must be defined in the ``_states`` method.

        The initial state does not need to be included in the list, it
        is implicit as we assume that any state can go back to the initial
        state in case of unrecoverable error.
        """
        response_schema = {
            "message": {
                "type": "dict",
                "required": False,
                "schema": {
                    "message_type": {
                        "type": "string",
                        "required": True,
                        "allowed": ["info", "warning", "error", "success"],
                    },
                    "body": {"type": "string", "required": True},
                },
            },
            "popup": {
                "type": "dict",
                "required": False,
                "schema": {"body": {"type": "string", "required": True}},
            },
            "log_entry_url": {"type": "string", "required": False},
        }
        if not data_schema:
            data_schema = {}

        # TODO: shall we keep `next_state` as part of base module?
        # In theory the next state is what leads users to the next step.
        if next_states:
            next_states = set(next_states)
            next_states.add(self._start_state)
            states_schemas = self._states()
            if self._start_state not in states_schemas:
                raise ValueError(
                    "the _start_state is {} but this state does not exist"
                    ", you may want to change the property's value".format(
                        self._start_state
                    )
                )
            unknown_states = set(next_states) - states_schemas.keys()
            if unknown_states:
                raise ValueError(
                    "states {!r} are not defined in _states".format(unknown_states)
                )

            data_schema = data_schema.copy()
            data_schema.update(
                {
                    state: {"type": "dict", "schema": states_schemas[state]}
                    for state in next_states
                }
            )
            response_schema["next_state"] = {"type": "string", "required": False}

        response_schema["data"] = {
            "type": "dict",
            "required": False,
            "schema": data_schema,
        }
        return response_schema
