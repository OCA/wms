# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.addons.component.core import Component


class ShopfloorSchemaDetailAction(Component):
    _inherit = "shopfloor.schema.detail.action"

    def location_detail(self):
        schema = self.location()
        schema.update(
            {
                "complete_name": {
                    "type": "string",
                    "nullable": False,
                    "required": True,
                },
                "reserved_move_lines": self._schema_list_of(self.move_line()),
            }
        )
        return schema

    def picking_detail(self):
        schema = self.picking()
        schema.update(
            {
                "picking_type_code": {
                    "type": "string",
                    "nullable": True,
                    "required": False,
                },
                "priority": {"type": "string", "nullable": True, "required": False},
                "operation_type": self._schema_dict_of(self._simple_record()),
                "move_lines": self._schema_list_of(self.move_line()),
            }
        )
        return schema

    def package_detail(self):
        schema = self.package(with_packaging=True)
        schema.update(
            {
                "pickings": self._schema_list_of(self.picking()),
                "move_lines": self._schema_list_of(self.move_line()),
                "location": self._schema_dict_of(self._simple_record()),
            }
        )
        return schema

    def lot_detail(self):
        schema = self.lot()
        schema.update(
            {
                "removal_date": {"type": "string", "nullable": True, "required": False},
                "expire_date": {"type": "string", "nullable": True, "required": False},
                "product": self._schema_dict_of(self.product_detail()),
                # TODO: packaging
            }
        )
        return schema

    def product(self):
        schema = super().product()
        schema.update(
            {
                "qty_available": {"type": "float", "required": True},
                "qty_reserved": {"type": "float", "required": True},
            }
        )
        return schema

    def product_detail(self):
        schema = self.product()
        schema.update(
            {
                "image": {"type": "string", "nullable": True, "required": False},
                "manufacturer": self._schema_dict_of(self._simple_record()),
                "suppliers": self._schema_list_of(self.product_supplierinfo()),
            }
        )
        return schema

    def product_supplierinfo(self):
        return {
            "id": {"required": True, "type": "integer"},
            "partner": {"type": "string", "nullable": True, "required": False},
            "product_name": {"type": "string", "nullable": True, "required": False},
            "product_code": {"type": "string", "nullable": True, "required": False},
        }

    def packaging_detail(self):
        schema = self.packaging()
        schema.update(
            {
                "length": {"type": "float", "nullable": True, "required": False},
                "width": {"type": "float", "nullable": True, "required": False},
                "height": {"type": "float", "nullable": True, "required": False},
                "max_weight": {"type": "float", "nullable": True, "required": False},
                "length_uom": {"type": "string", "nullable": True, "required": False},
                "weight_uom": {"type": "string", "nullable": True, "required": False},
                "barcode": {"type": "string", "nullable": True, "required": False},
            }
        )
        return schema
