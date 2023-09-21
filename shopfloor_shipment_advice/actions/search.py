# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from odoo.addons.component.core import Component


class SearchAction(Component):
    _inherit = "shopfloor.search.action"

    def dock_from_scan(self, barcode):
        model = self.env["stock.dock"]
        if not barcode:
            return model.browse()
        return model.search(
            ["|", ("barcode", "=", barcode), ("name", "=", barcode)], limit=1
        )

    def shipment_from_scan(self, barcode):
        model = self.env["shipment.advice"]
        if not barcode:
            return model.browse()
        return model.search(
            [("name", "=", barcode)],
            limit=1,
        )

    @property
    def _barcode_type_handler(self):
        res = super()._barcode_type_handler
        res["dock"] = self.dock_from_scan
        res["shipment"] = self.shipment_from_scan
        return res
