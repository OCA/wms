# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
from odoo.addons.component.core import Component


class ShopfloorSchemaAction(Component):
    _inherit = "shopfloor.schema.action"

    def package(self, with_packaging=False):
        res = super().package(with_packaging)
        res.update(
            {
                "height": {"required": True, "nullable": True, "type": "float"},
                "length": {"required": True, "nullable": True, "type": "float"},
                "width": {"required": True, "nullable": True, "type": "float"},
            }
        )
        return res
