# Copyright 2021 ACSONE SA/NV (http://www.acsone.eu)
# @author Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.component.core import Component


class ScanPartnerHandler(Component):
    """Scan anything handler for res.partner."""

    _name = "shopfloor.scan.partner.handler"
    _inherit = "shopfloor.scan.anything.handler"

    record_type = "partner_example"

    def search(self, identifier):
        return self._search.partner_from_scan(identifier)

    @property
    def converter(self):
        return self._data_detail.partner_detail

    def schema(self):
        return self._schema_detail.partner_detail()
