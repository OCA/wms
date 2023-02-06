# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# Copyright 2021 ACSONE SA/NV (http://www.acsone.eu)
# @author Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.component.core import Component


class LocationHandler(Component):
    """Scan anything handler for stock.location."""

    _name = "shopfloor.scan.location.handler"
    _inherit = "shopfloor.scan.anything.handler"

    record_type = "location"

    def search(self, identifier):
        res = self._search.find(identifier, types=("location",))
        return res.record if res.record else self.env["stock.location"]

    @property
    def converter(self):
        return self._data_detail.location_detail

    def schema(self):
        return self._schema_detail.location_detail()
