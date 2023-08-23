# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.addons.component.core import Component


class ShopfloorSchemaAction(Component):
    _inherit = "shopfloor.schema.action"

    def purchase_order(self):
        return {
            "id": {"required": True, "type": "integer"},
            "name": {"type": "string", "nullable": False, "required": True},
            "partner_ref": {"type": "string", "nullable": True, "required": False},
        }

    def picking(self, **kw):
        res = super().picking(**kw)
        res.update(
            {
                "purchase_order": self._schema_dict_of(
                    self.purchase_order(), required=False
                )
            }
        )
        return res
