from odoo.addons.component.core import AbstractComponent


class BaseShopfloorValidatorResponse(AbstractComponent):
    _inherit = "base.shopfloor.validator.response"

    def _get_global_fields_schemas(self) -> dict:
        res = super()._get_global_fields_schemas()
        res.update(
            {
                "allow_print_label": {
                    "type": "boolean",
                    "nullable": True,
                }
            }
        )
        return res
