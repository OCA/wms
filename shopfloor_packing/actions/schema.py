# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class ShopfloorSchemaAction(Component):

    _inherit = "shopfloor.schema.action"

    def package(self, with_packaging=False):
        schema = super().package(with_packaging=with_packaging)
        schema["is_internal"] = {"required": False, "type": "boolean"}
        return schema
