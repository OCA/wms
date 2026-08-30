# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from odoo.addons.component.core import Component


class ShopfloorSchemaDetailAction(Component):

    _inherit = "shopfloor.schema.detail.action"

    def shipment_advice_detail(self):
        schema = self.shipment_advice()
        schema["planned_moves"] = self._schema_list_of(self.move())
        return schema
