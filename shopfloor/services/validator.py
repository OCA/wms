# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.addons.component.core import AbstractComponent


class BaseShopfloorValidator(AbstractComponent):
    """Base class for Validators"""

    _inherit = "base.rest.service"
    _name = "base.shopfloor.validator"
    _collection = "shopfloor.service"
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
    _collection = "shopfloor.service"
    _is_rest_service_component = False

    # Initial state of a workflow
    _start_state = "start"

    def _states(self):
        """List of possible next states

        With the schema of the data send to the client to transition
        to the next state.
        """
        return {}

    @property
    def schemas(self):
        return self.component(usage="schema")

    @property
    def schemas_detail(self):
        return self.component(usage="schema_detail")

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
