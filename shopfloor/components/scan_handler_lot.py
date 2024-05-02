# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# Copyright 2021 ACSONE SA/NV (http://www.acsone.eu)
# @author Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.component.core import Component


class LotHandler(Component):
    """Scan anything handler for stock.lot."""

    _name = "shopfloor.scan.lot.handler"
    _inherit = "shopfloor.scan.anything.handler"

    record_type = "lot"

    def search(self, identifier):
        res = self._search.find(identifier, types=("lot",))
        return res.record if res.record else self.env["stock.lot"]

    @property
    def converter(self):
        return self._data_detail.lot_detail

    def schema(self):
        return self._schema_detail.lot_detail()
