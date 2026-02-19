from odoo.addons.component.core import Component


class ShopfloorSchemaAction(Component):
    _inherit = "shopfloor.schema.action"

    def packaging_dimensions(self):
        return {
            "id": {"required": True, "type": "integer"},
            "name": {"type": "string", "nullable": False, "required": True},
            "qty": {"type": "float", "required": True},
            "length": {"type": "float", "nullable": True, "required": False},
            "width": {"type": "float", "nullable": True, "required": False},
            "height": {"type": "float", "nullable": True, "required": False},
            "weight": {"type": "float", "nullable": True, "required": False},
            "length_uom_name": {
                "type": "string",
                "nullable": True,
                "required": False,
            },
            "weight_uom_name": {
                "type": "string",
                "nullable": True,
                "required": False,
            },
            "barcode": {"type": "string", "nullable": True, "required": False},
        }
