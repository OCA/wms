# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.component.core import Component


class ShopfloorSchemaDetailAction(Component):
    _inherit = "shopfloor.schema.detail.action"

    def product_detail(self):
        res = super().product_detail()
        res["manufacturer"] = self._schema_dict_of(self._simple_record())
        return res
