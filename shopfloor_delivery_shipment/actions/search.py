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
