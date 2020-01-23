from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import Component


class ShopfloorPack(Component):
    """Expose data about Stock Quant Packages"""

    _inherit = "base.shopfloor.service"
    _name = "shopfloor.pack"
    _usage = "pack"
    _description = __doc__

    def get_by_name(self, pack_name):
        """
        Get pack informations
        """
        pack = self.env["stock.quant.package"].search(
            [("name", "=", pack_name)],
            # TODO, is it what we want? error if not found?
            limit=1,
        )
        return self._to_json(pack)[:1]

    def _validator_get_by_name(self):
        return {"pack_name": {"type": "string", "nullable": False, "required": True}}

    def _validator_return_get_by_name(self):
        return {"data": self._record_return_schema}

    def _convert_one_record(self, record):
        return {
            "id": record.id,
            "name": record.name,
            "location": {"id": record.location_id.id, "name": record.location_id.name},
        }

    @property
    def _record_return_schema(self):
        return {
            "type": "dict",
            "schema": {
                "id": {"coerce": to_int, "required": True, "type": "integer"},
                "name": {"type": "string", "nullable": False, "required": True},
                "location": {
                    "type": "dict",
                    "schema": {
                        "id": {"coerce": to_int, "required": True, "type": "integer"},
                        "name": {"type": "string", "nullable": False, "required": True},
                    },
                },
            },
        }
