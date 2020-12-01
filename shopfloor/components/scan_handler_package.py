# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# Copyright 2021 ACSONE SA/NV (http://www.acsone.eu)
# @author Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.component.core import Component


class PackageHandler(Component):
    """Scan anything handler for stock.quant.package."""

    _name = "shopfloor.scan.package.handler"
    _inherit = "shopfloor.scan.anything.handler"

    record_type = "package"

    def search(self, identifier):
        return self._search.package_from_scan(identifier)

    @property
    def converter(self):
        return self._data_detail.package_detail

    def schema(self):
        return self._schema_detail.package_detail()
