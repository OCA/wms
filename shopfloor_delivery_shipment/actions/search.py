# Copyright 2021 Camptocamp SA
# Copyright 2026 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from odoo.osv import expression

from odoo.addons.component.core import Component


class SearchAction(Component):
    _inherit = "shopfloor.search.action"

    def dock_from_scan(self, barcode, warehouses=None):
        model = self.env["stock.dock"]
        if not barcode:
            return model.browse()
        domain = ["|", ("barcode", "=", barcode), ("name", "=", barcode)]
        if warehouses:
            domain = expression.AND([domain, [("warehouse_id", "in", warehouses.ids)]])
        return model.search(domain, limit=1)
