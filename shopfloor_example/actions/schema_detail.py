# Copyright 2021 ACSONE SA/NV (http://www.acsone.eu)
# @author Simone Orsi <simahawk@gmail.com>
# # License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.addons.component.core import Component


class ShopfloorSchemaDetailAction(Component):
    _inherit = "shopfloor.schema.detail.action"

    def partner_detail(self):
        schema = self._simple_record()
        schema.update(
            {
                "ref": {"type": "string", "nullable": True, "required": True},
                "email": {"type": "string", "nullable": True, "required": False},
            }
        )
        return schema
