from odoo.osv import expression

from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import Component


class ShopfloorLocation(Component):
    """Expose Stock Locations data for the current warehouse."""

    _inherit = "base.shopfloor.service"
    _name = "shopfloor.location"
    _usage = "location"
    _expose_model = "stock.location"
    _description = __doc__

    def search(self, name_fragment=None):
        """List available locations for current user"""
        domain = self._get_base_search_domain()
        if name_fragment:
            domain = expression.AND(
                [
                    domain,
                    [
                        "|",
                        ("name", "ilike", name_fragment),
                        ("barcode", "ilike", name_fragment),
                    ],
                ]
            )
        records = self.env[self._expose_model].search(domain)
        return self._response(
            data={"size": len(records), "records": self._to_json(records)}
        )

    def _get_base_search_domain(self):
        # TODO add filter on warehouse of the current profile
        return super()._get_base_search_domain()

    def _convert_one_record(self, record):
        return {
            "id": record.id,
            "name": record.name,
            "complete_name": record.complete_name,
            "barcode": record.barcode or "",
        }


class ShopfloorLocationValidator(Component):
    """Validators for the Location endpoints"""

    _inherit = "base.shopfloor.validator"
    _name = "shopfloor.location.validator"
    _usage = "location.validator"

    def search(self):
        return {
            "name_fragment": {"type": "string", "nullable": True, "required": False}
        }


class ShopfloorLocationValidatorResponse(Component):
    """Validators for the Location endpoints responses"""

    _inherit = "base.shopfloor.validator.response"
    _name = "shopfloor.location.validator.response"
    _usage = "location.validator.response"

    def search(self):
        return self._response_schema(
            {
                "size": {"coerce": to_int, "required": True, "type": "integer"},
                "records": {
                    "type": "list",
                    "schema": {
                        "type": "dict",
                        "schema": {
                            "id": {
                                "coerce": to_int,
                                "required": True,
                                "type": "integer",
                            },
                            "name": {
                                "type": "string",
                                "nullable": False,
                                "required": True,
                            },
                            "complete_name": {
                                "type": "string",
                                "nullable": False,
                                "required": True,
                            },
                            "barcode": {
                                "type": "string",
                                "nullable": False,
                                "required": False,
                            },
                        },
                    },
                },
            }
        )
