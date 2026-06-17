# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class ShopfloorSchemaAction(Component):
    _inherit = "shopfloor.schema.action"

    def picking(self):
        res = super().picking()

        res.update(
            {"docks": self._schema_list_of(self._simple_record(), required=False)}
        )

        return res
