# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from odoo.addons.component.core import Component


class ShopfloorSchemaAction(Component):

    _inherit = "shopfloor.schema.action"

    def shipment_advice(self):
        return {
            "id": {"required": True, "type": "integer"},
            "name": {"type": "string", "nullable": False, "required": True},
            "dock": self._schema_dict_of(self.dock()),
            "state": {"type": "string", "nullable": False, "required": True},
            "is_planned": {"type": "boolean", "nullable": False, "required": True},
        }

    def dock(self):
        return self._simple_record()

    def picking_loaded(self):
        schema = self.picking()
        schema.update(
            {
                "loaded_progress_f": {
                    "type": "float",
                    "nullable": False,
                    "required": True,
                },
                "loaded_progress": {
                    "type": "string",
                    "nullable": False,
                    "required": True,
                },
                "is_fully_loaded": {
                    "type": "boolean",
                    "nullable": False,
                    "required": True,
                },
                "is_partially_loaded": {
                    "type": "boolean",
                    "nullable": False,
                    "required": True,
                },
            }
        )
        return schema

    def shipment_lading_summary(self):
        return {
            "loaded_pickings_count": {
                "type": "integer",
                "nullable": False,
                "required": True,
            },
            "loaded_packages_count": {
                "type": "integer",
                "nullable": False,
                "required": True,
            },
            "total_packages_count": {
                "type": "integer",
                "nullable": False,
                "required": True,
            },
            "loaded_bulk_lines_count": {
                "type": "integer",
                "nullable": False,
                "required": True,
            },
            "total_bulk_lines_count": {
                "type": "integer",
                "nullable": False,
                "required": True,
            },
            "loaded_weight": {"type": "integer", "nullable": False, "required": True},
        }

    def shipment_on_dock_summary(self):
        return {
            "total_pickings_count": {
                "type": "integer",
                "nullable": False,
                "required": True,
            },
            "total_packages_count": {
                "type": "integer",
                "nullable": False,
                "required": True,
            },
            "total_bulk_lines_count": {
                "type": "integer",
                "nullable": False,
                "required": True,
            },
        }
