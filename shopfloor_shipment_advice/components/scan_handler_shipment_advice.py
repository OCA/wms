# Copyright 2023 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.component.core import Component


class ShipmentHandler(Component):
    """Scan anything handler for shipment.advice."""

    _name = "shopfloor.scan.shipment.handler"
    _inherit = "shopfloor.scan.anything.handler"

    record_type = "shipment"

    def search(self, identifier):
        res = self._search.find(identifier, types=("shipment",))
        return res.record if res.record else self.env["shipment.advice"]

    @property
    def converter(self):
        return self._data_detail.shipment_advice_detail

    def schema(self):
        return self._schema_detail.shipment_advice_detail()
