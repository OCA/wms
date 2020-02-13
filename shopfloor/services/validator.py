from odoo.addons.component.core import AbstractComponent


class BaseShopfloorValidator(AbstractComponent):
    """Base class for Validators"""

    _inherit = "base.rest.service"
    _name = "base.shopfloor.validator"
    _collection = "shopfloor.service"
    _is_rest_service_component = False


class BaseShopfloorValidatorResponse(AbstractComponent):
    """Base class for Validator for Responses"""

    _inherit = "base.rest.service"
    _name = "base.shopfloor.validator.response"
    _collection = "shopfloor.service"
    _is_rest_service_component = False

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
            "next_state": {"type": "string", "required": False},
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
