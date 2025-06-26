# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.addons.component.core import Component


class ShopfloorSchemaAction(Component):
    _inherit = "shopfloor.schema.action"

    def move_line(self, with_packaging=False, with_picking=False):
        schema = super().move_line(with_packaging, with_picking)
        schema.update(
            {
                "location_destination_suggestions": {
                    "type": "string",
                    "nullable": True,
                    "required": False,
                },
            }
        )
        return schema
