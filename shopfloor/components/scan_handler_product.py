# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# Copyright 2021 ACSONE SA/NV (http://www.acsone.eu)
# @author Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.component.core import Component


class ProductHandler(Component):
    """Scan anything handler for product.product."""

    _name = "shopfloor.scan.product.handler"
    _inherit = "shopfloor.scan.anything.handler"

    record_type = "product"

    def search(self, identifier):
        res = self._search.find(identifier, types=("product", "packaging"))
        if res.record and res.type == "packaging":
            return res.record.product_id
        return res.record if res.record else self.env["product.product"]

    @property
    def converter(self):
        return self._data_detail.product_detail

    def schema(self):
        return self._schema_detail.product_detail()
