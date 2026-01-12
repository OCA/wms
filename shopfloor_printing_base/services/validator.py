from odoo.addons.component.core import AbstractComponent


class BaseShopfloorValidatorResponse(AbstractComponent):
    _inherit = "base.shopfloor.validator.response"

    def _response_schema(self, data_schema=None, next_states=None):
        data_schema = data_schema or {}
        data_schema.update({"allow_print_label": {"type": "boolean", "nullable": True}})

        return super()._response_schema(
            data_schema=data_schema, next_states=next_states
        )
